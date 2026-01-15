#![cfg_attr(
    all(windows, not(feature = "console")),
    windows_subsystem = "windows"
)]
use std::fs::{self};
use std::fs::File;
use std::env;
use std::time::{SystemTime, UNIX_EPOCH};
use anyhow::{Result, anyhow};
use std::path::{Path, PathBuf};
use std::process::Command;
use std::process::id;

static ZIP_PASSWORD: &str = "PyCompyle";

struct Options {
    pub exe: PathBuf,
    pub debug: bool
}

fn generate_unique_output_dir() -> Result<String> {
    let base_path = env::var("TEMP").unwrap_or_else(|_| {
        #[cfg(target_os = "windows")] { r"C:\Windows\TEMP".to_string() }
        #[cfg(target_os = "linux")] { "/tmp".to_string() }
        #[cfg(not(any(target_os = "windows", target_os = "linux")))] { return Err(anyhow!("unsupported platform")) }
    });
    let now = SystemTime::now();
    let since_epoch = now.duration_since(UNIX_EPOCH).unwrap();
    let timestamp = since_epoch.as_secs();

    let pid = id();

    Ok(format!("{}\\mrb36.{}.{}", base_path, timestamp, pid))
}

fn extract_embedded_zip(output_dir: &Path, password: &str, options: &Options) -> Result<()> {
    
    let file = File::open(options.exe.clone())?;
    let mut archive = zip::ZipArchive::new(file)?;

    if options.debug {
        println!("Extracting embedded zip");
    }

    let names: Vec<String> = archive.file_names().map(|s| s.to_owned()).collect();
    
    for file_name in names {
        let mut entry = archive.by_name_decrypt(&file_name, password.as_bytes())?;
        let outpath = output_dir.join(entry.name());

        if entry.is_dir() {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(parent) = outpath.parent() {
                fs::create_dir_all(parent)?;
            }
            let mut outfile = File::create(&outpath)?;
            std::io::copy(&mut entry, &mut outfile)?;
        }

    }
    
    Ok(())
}


fn add_sys_mod(output_dir: &Path, script_path: &Path, options: &Options) -> Result<()> {
    let exe = options.exe.to_string_lossy();

    let new_text = format!(
        "import sys\nsys.argv[0] = r'{}'\nsys.executable = r'{}'\nsys.path.insert(0, r'{}')\n",
        exe, exe, output_dir.to_string_lossy()
    );

    let marker_comment = "# PyCompyle custom sys injection above DO NOT EDIT\n";

    let original = fs::read_to_string(script_path)?;

    let modified = if let Some((_, after)) = original.split_once(marker_comment) {
        format!("{}{}{}", new_text, marker_comment, after.trim_start())
    } else {
        format!("{}{}{}", new_text, marker_comment, original)
    };

    fs::write(script_path, modified)?;
    Ok(())
}

fn run_extracted_executable(output_dir: &Path, options: &Options) -> Result<()> {
    #[cfg(target_os = "windows")]
    let python_executable = output_dir.join("python.exe");
    #[cfg(target_os = "linux")]
    let python_executable = output_dir.join("python");

    let script_path = output_dir.join("__main__.py");
    

    if !Path::new(&script_path).exists() {
        eprintln!("Error: __main__.py missing");
        return Err(anyhow!("Error: __main__.py missing"));
    }
    
    add_sys_mod(output_dir, &script_path, options)?;
    
    let mut pyargs = vec!["-B".to_string()];
    let pyargs_file = format!("{:?}/pyargs", output_dir);

    // If pyargs file exists, read arguments from it
    if Path::new(&pyargs_file).exists() {
        pyargs.clear();
        if let Ok(contents) = fs::read_to_string(&pyargs_file) {
            for line in contents.lines() {
                pyargs.extend(line.split_whitespace().map(|s| s.to_string()));
            }
        }
    }

    // Additional args from command line
    let additional_args: Vec<String> = env::args().skip(1).collect();

    if options.debug {
        println!("Starting embedded Python");
    }

    // Make sure python executable is executable (Linux)
    #[cfg(target_os = "linux")]
    {
        use std::os::unix::fs::PermissionsExt;
        let mut perms = fs::metadata(&python_executable)?.permissions();
        perms.set_mode(0o755);
        fs::set_permissions(&python_executable, perms)?;
    }

    // Run python process
    let mut cmd = Command::new(python_executable);
    cmd.args(&pyargs)
        .arg(script_path)
        .args(&additional_args);

    match cmd.status() {
        Ok(status) => {
            if options.debug {
                println!("Python exited with: {}", status);
            }
            Ok(())
        },
        Err(e) => {
            if options.debug {
            eprintln!("Failed to run Python: {}", e);
        }
            Err(anyhow!("{}", e))
        },
    }
}

fn cleanup_directory(output_dir: &Path) -> bool {
    fs::remove_dir_all(output_dir).is_ok()
}

#[cfg(target_os = "windows")]
fn schedule_startup_folder_deletion(output_dir: &Path) -> Result<PathBuf> {
    let appdata = env::var("APPDATA")?;
    let appdata = Path::new(&appdata);

    let folder_name = output_dir.file_name().ok_or_else(|| anyhow!("output directory ended in .. which is invalid"))?;

    let startup_dir = appdata.join(r#"Microsoft\Windows\Start Menu\Programs\Startup"#);

    let name = format!("delete_{}.bat", folder_name.to_string_lossy());

    let bat_path = startup_dir.join(&name);

    let name_str = output_dir.to_string_lossy();

    let code = format!("@echo off\nif exist \"{name_str}\" rmdir /s /q \"{name_str}\"\ndel \"%~f0\"");

    fs::write(&bat_path, &code)?;

    Ok(bat_path)
}
    
fn main() -> Result<()> {
    let options = Options {
        exe: std::env::current_exe()?,
        debug: match env::var("PYCOMPYLEDEBUG") {
            Ok(v) => {
                v == "1"
            },
            Err(_) => false
        },
    };
    
    if options.debug {
        println!("Bootloader started");
    }

    let output_dir = generate_unique_output_dir()?;
    let output_dir = Path::new(&output_dir);
    

    #[allow(unused_assignments)]
    let mut bat_path: Option<PathBuf> = None;

    match extract_embedded_zip(output_dir, ZIP_PASSWORD, &options) {
        Ok(_) => {
            #[cfg(target_os = "windows")]
            {
                bat_path = Some(schedule_startup_folder_deletion(output_dir)?);
            }
            
            run_extracted_executable(output_dir, &options)?;

            let cleanup = cleanup_directory(output_dir);

            if cleanup && let Some(bat) = bat_path {
                fs::remove_file(bat)?
            }

        }
        Err(e) => {

            let pth = options.exe.parent().ok_or_else(|| anyhow!("asd"))?.join("__main__.py");
            if pth.exists() {
                run_extracted_executable(&pth.parent().unwrap(), &options)?;
            } else {
                return Err(anyhow!("Error: {e}"))
            }

        }
    }

    Ok(())
}
