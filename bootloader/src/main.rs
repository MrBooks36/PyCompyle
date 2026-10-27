#![cfg_attr(all(windows, not(feature = "console")), windows_subsystem = "windows")]
use anyhow::{Result, anyhow};
use std::env;
use std::fs::File;
use std::fs::{self};
use std::path::{Path, PathBuf};
use std::process::id;
use std::process::{Command, ExitStatus};
use std::time::{SystemTime, UNIX_EPOCH};

#[cfg(all(target_os = "windows", not(feature = "console")))]
use std::os::windows::process::CommandExt;

struct Options {
    pub exe: PathBuf,
    pub debug: bool,
}

fn generate_unique_output_dir() -> Result<PathBuf> {
    let base_path = env::temp_dir();
    let timestamp = SystemTime::now().duration_since(UNIX_EPOCH)?.as_secs();
    let pid = id();

    Ok(base_path.join(format!("mrb36.{}.{}", timestamp, pid)))
}

fn extract_embedded_zip(output_dir: &Path, options: &Options) -> Result<()> {
    const PASSWORD: &[u8] = b"PyCompyle";

    let file = File::open(&options.exe)?;
    let mut archive = zip::ZipArchive::new(file)?;

    if options.debug {
        println!("Extracting embedded zip");
    }

    for i in 0..archive.len() {
        let mut entry = archive.by_index_decrypt(i, PASSWORD)?;

        let entry_name = entry
            .enclosed_name()
            .ok_or_else(|| anyhow!("Malicious zip path detected"))?;
        let outpath = output_dir.join(entry_name);

        if entry.is_dir() {
            fs::create_dir_all(&outpath)?;
        } else {
            if let Some(p) = outpath.parent() {
                fs::create_dir_all(p)?;
            }
            let mut outfile = File::create(&outpath)?;
            std::io::copy(&mut entry, &mut outfile)?;
        }
    }
    Ok(())
}

fn add_sys_mod(script_path: &Path, options: &Options) -> Result<()> {
    let exe = options.exe.to_string_lossy();

    let new_text = format!(
        "import sys\nsys.argv[0] = r'{}'\nsys.executable = r'{}'\n",
        exe, exe
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

fn run_extracted_executable(output_dir: &Path, options: &Options) -> Result<ExitStatus> {
    #[cfg(target_os = "windows")]
    let python_executable = output_dir.join("python.exe");
    #[cfg(target_os = "linux")]
    let python_executable = output_dir.join("python");

    let script_path = output_dir.join("__main__.py");

    if !script_path.exists() {
        eprintln!("Error: __main__.py missing");
        return Err(anyhow!("Error: __main__.py missing"));
    }

    add_sys_mod(&script_path, options)?;

    let mut pyargs = vec!["-B".to_string()];

    let pyargs_file = output_dir.join("pyargs");

    // If pyargs file exists, read arguments from it
    if pyargs_file.exists() {
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
    cmd.args(&pyargs).arg(script_path).args(&additional_args);

    #[cfg(all(target_os = "windows", not(feature = "console")))]
    // 0x08000000 is the Win32 constant for CREATE_NO_WINDOW
    cmd.creation_flags(0x08000000);

    match cmd.status() {
        Ok(status) => {
            if options.debug {
                println!("Python exited with: {}", status);
            }
            Ok(status)
        }
        Err(e) => {
            if options.debug {
                eprintln!("Failed to run Python: {}", e);
            }
            Err(anyhow!("{}", e))
        }
    }
}

fn cleanup_directory(output_dir: &Path) -> bool {
    fs::remove_dir_all(output_dir).is_ok()
}

fn main() -> Result<()> {
    let options = Options {
        exe: std::env::current_exe()?,
        debug: match env::var("PYCOMPYLEDEBUG") {
            Ok(v) => v == "1",
            Err(_) => false,
        },
    };

    if options.debug {
        println!("Bootloader started");
    }

    let output_dir = generate_unique_output_dir()?;

    // Track the final exit status of Python
    let exit_status = match extract_embedded_zip(&output_dir, &options) {
        Ok(_) => {
            let status = run_extracted_executable(&output_dir, &options)?;
            cleanup_directory(&output_dir);
            status // Return the status
        }
        Err(e) => {
            let pth = options
                .exe
                .parent()
                .ok_or_else(|| anyhow!("asd"))?
                .join("__main__.py");
            if pth.exists() {
                run_extracted_executable(pth.parent().unwrap(), &options)? // Return the status
            } else {
                return Err(anyhow!("Error: {e}"));
            }
        }
    };

    // Extract code integer or fallback to 1 if terminated by a signal
    let exit_code = exit_status.code().unwrap_or(1);

    std::process::exit(exit_code);
}
