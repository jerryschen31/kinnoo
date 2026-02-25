"""
CLI entry point for kinnoo.
Handles argument parsing and dispatches subcommands.
"""

import argparse
import sys
import re
from pathlib import Path
import traceback
import yaml

try:
    from kinnoo.schema import NAME_PATTERN
except ImportError:
    # fallback for direct script execution
    from .schema import NAME_PATTERN

def main():
    import os
    parser = argparse.ArgumentParser(prog="kinnoo", description="Kinnoo CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # init subcommand
    init_parser = subparsers.add_parser("init", help="Scaffold a new kinnoo agent")
    init_parser.add_argument("agent_name", nargs="?", help="Name of the agent to create")
    init_parser.add_argument(
        "--framework",
        choices=["gemini", "chatgpt", "claude-chat"],
        help="(Optional) Pre-populate agent with LLM framework template (gemini, chatgpt, claude-chat)"
    )

    # Add 'run' subcommand
    run_parser = subparsers.add_parser("run", help="Run a kinnoo agent")
    run_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory")
    run_parser.add_argument("input", nargs="?", help="Input string to pass to the agent entrypoint")

    # Add 'install' subcommand
    install_parser = subparsers.add_parser("install", help="Install a kinnoo agent archive (.kno)")
    install_parser.add_argument("archive_path", nargs="?", help="Path to .kno archive to install")

    # Add 'pack' subcommand
    pack_parser = subparsers.add_parser("pack", help="Package an agent directory into a .kno archive")
    pack_parser.add_argument("agent_dir", nargs="?", help="Path to agent directory to package")

    # Pre-parse sys.argv for missing args to print custom usage before argparse error
    if len(sys.argv) > 1 and sys.argv[1] == "run":
        if len(sys.argv) < 4:
            print("Usage: kinnoo run <agent-dir> '<input>'", file=sys.stderr)
            sys.exit(1)

    args = parser.parse_args()

    if args.command == "init":
        if not args.agent_name:
            print("Usage: kinnoo init <agent-name>", file=sys.stderr)
            sys.exit(1)
        if not re.match(NAME_PATTERN, args.agent_name):
            print(f"Error: Invalid agent name '{args.agent_name}'. Must match pattern: {NAME_PATTERN}", file=sys.stderr)
            sys.exit(1)
        from kinnoo.init_command import init_agent
        # from pathlib import Path
        try:
            init_agent(args.agent_name, Path.cwd(), framework=args.framework)
            print(f"Initialized agent: {args.agent_name}")
        except FileExistsError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)


    elif args.command == "run":
        # ...existing run logic...
        agent_dir = Path(args.agent_dir).resolve()
        venv_dir = agent_dir / ".venv"
        requirements = agent_dir / "requirements.txt"
        kinnoo_yaml = agent_dir / "kinnoo.yaml"
        import subprocess

        if not hasattr(args, "agent_dir") or args.agent_dir is None or args.input is None:
            print("Usage: kinnoo run <agent-dir> '<input>'", file=sys.stderr)
            sys.exit(1)
        
        # Ensure .venv exists (task8, assumed done)
        if not venv_dir.exists():
            import venv
            try:
                venv.create(venv_dir, with_pip=True)
            except PermissionError as e:
                print(f"Error: Permission denied while creating .venv in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error: Failed to create .venv in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)

        if requirements.exists() and requirements.read_text().strip():
            pip_exe = venv_dir / "bin" / "pip"
            if not pip_exe.exists():
                pip_exe = venv_dir / "Scripts" / "pip.exe"  # Windows fallback
            if not pip_exe.exists():
                print(f"Error: pip not found in venv at {pip_exe}", file=sys.stderr)
                sys.exit(1)
            print("[kinnoo] installing requirements for running agent...")
            try:
                result = subprocess.run(
                    [str(pip_exe), "install", "-r", str(requirements)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
            except PermissionError as e:
                print(f"Error: Permission denied while installing requirements in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            except Exception as e:
                print(f"Error: Failed to install requirements in {agent_dir}: {e}", file=sys.stderr)
                sys.exit(1)
            if result.returncode != 0:
                print("Error: Failed to install requirements for running agent. Please check your requirements.txt and try again.", file=sys.stderr)
                sys.exit(result.returncode)

        # Validate kinnoo.yaml manifest (task7, assumed done)
        if not kinnoo_yaml.exists():
            print(f"Error: kinnoo.yaml not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)

        # Parse kinnoo.yaml to get entrypoint
        try:
            with open(kinnoo_yaml, "r") as f:
                try:
                    manifest = yaml.safe_load(f)
                except yaml.YAMLError as ye:
                    print(f"Error: kinnoo.yaml is corrupted or invalid YAML: {ye}", file=sys.stderr)
                    sys.exit(1)
        except PermissionError as e:
            print(f"Error: Permission denied while reading kinnoo.yaml: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error parsing kinnoo.yaml: {e}", file=sys.stderr)
            sys.exit(1)

        entrypoint = manifest.get("entrypoint")
        if not entrypoint:
            print("Error: 'entrypoint' not specified in kinnoo.yaml", file=sys.stderr)
            sys.exit(1)

        entrypoint_path = agent_dir / entrypoint
        if not entrypoint_path.exists():
            print(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)

        # Find python executable in venv
        python_exe = venv_dir / "bin" / "python"
        if not python_exe.exists():
            python_exe = venv_dir / "Scripts" / "python.exe"  # Windows fallback
        if not python_exe.exists():
            print(f"Error: python not found in venv at {python_exe}", file=sys.stderr)
            sys.exit(1)

        # Prepare input argument
        input_arg = args.input if args.input is not None else ""

        process = subprocess.Popen(
            [str(python_exe), str(entrypoint_path), input_arg],
            cwd=agent_dir,
            stdout=sys.stdout,
            stderr=sys.stderr
        )
        process.communicate()
        sys.exit(process.returncode)

    elif args.command == "install":
        # Task29: Argument parsing and usage error for kinnoo install
        # The install subcommand expects a .kno archive path as argument
        archive_path = getattr(args, "archive_path", None)
        if archive_path is None:
            print("Usage: kinnoo install <archive-path>", file=sys.stderr)
            sys.exit(1)
        # --- Task30: Extract .kno archive to new directory with collision handling ---
        import zipfile
        archive_path = Path(archive_path)
        if not archive_path.exists() or not archive_path.is_file():
            print(f"Error: Archive '{archive_path}' does not exist or is not a file.", file=sys.stderr)
            sys.exit(1)
        if not str(archive_path).endswith(".kno"):
            print(f"Error: Archive '{archive_path}' is not a .kno file.", file=sys.stderr)
            sys.exit(1)

        # Target directory is archive name without .kno extension
        target_dir = archive_path.with_suffix("")
        if target_dir.exists():
            print(f"Error: Target directory '{target_dir}' already exists. Aborting to prevent overwrite.", file=sys.stderr)
            sys.exit(1)

        # Extract archive
        try:
            with zipfile.ZipFile(archive_path, "r") as z:
                z.extractall(target_dir)
        except zipfile.BadZipFile:
            print(f"Error: Archive '{archive_path}' is not a valid .kno (zip) archive.", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error: Failed to extract archive: {e}", file=sys.stderr)
            sys.exit(1)

        print(f"[kinnoo install] Extracted '{archive_path.name}' to '{target_dir}'")

        # --- Task31: Validate manifest before installation ---
        kinnoo_yaml_path = target_dir / "kinnoo.yaml"
        if not kinnoo_yaml_path.exists():
            print(f"Error: kinnoo.yaml not found in extracted directory '{target_dir}'. Aborting install.", file=sys.stderr)
            # Clean up extracted directory
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
            sys.exit(1)
        try:
            from kinnoo.validator import validate
        except ImportError:
            from .validator import validate
        try:
            is_valid, errors = validate(str(kinnoo_yaml_path))
        except Exception as e:
            print(f"Error: Failed to validate kinnoo.yaml: {e}", file=sys.stderr)
            import traceback
            traceback.print_exc()
            # Clean up extracted directory
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
            sys.exit(1)
        if not is_valid:
            print("Manifest validation failed:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            # Clean up extracted directory
            import shutil
            shutil.rmtree(target_dir, ignore_errors=True)
            sys.exit(1)
        print(f"[kinnoo install] Manifest validated successfully.")

    elif args.command == "pack":
        agent_dir = args.agent_dir
        if agent_dir is None:
            print("Usage: kinnoo pack <agent-dir>")
            sys.exit(1)
        abs_agent_dir = os.path.abspath(agent_dir)
        cwd = os.path.abspath(os.getcwd())
        if abs_agent_dir == cwd or os.path.samefile(abs_agent_dir, cwd):
            print("Do not run kinnoo pack from inside the agent directory. Please navigate outside and run: kinnoo pack <agent-dir>")
            sys.exit(1)
        if not os.path.isdir(abs_agent_dir):
            print(f"Error: Agent directory '{agent_dir}' does not exist.")
            sys.exit(1)

        # --- Task24: Manifest validation before packaging ---
        kinnoo_yaml_path = os.path.join(abs_agent_dir, "kinnoo.yaml")
        if not os.path.isfile(kinnoo_yaml_path):
            print(f"Error: kinnoo.yaml not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)
        try:
            from kinnoo.validator import validate
        except ImportError:
            from .validator import validate
        try:
            is_valid, errors = validate(kinnoo_yaml_path)
        except Exception as e:
            print(f"Error: Failed to validate kinnoo.yaml: {e}", file=sys.stderr)
            traceback.print_exc()
            sys.exit(1)
        if not is_valid:
            print("Manifest validation failed:", file=sys.stderr)
            for err in errors:
                print(f"  - {err}", file=sys.stderr)
            sys.exit(1)

        # --- Task25: Gather required files for packaging ---
        with open(kinnoo_yaml_path, "r") as f:
            manifest = yaml.safe_load(f)
        entrypoint = manifest.get("entrypoint")
        if not entrypoint:
            print("Error: 'entrypoint' not specified in kinnoo.yaml", file=sys.stderr)
            sys.exit(1)
        entrypoint_path = os.path.join(abs_agent_dir, entrypoint)
        if not os.path.isfile(entrypoint_path):
            print(f"Error: Entrypoint file '{entrypoint}' not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)
        requirements_path = os.path.join(abs_agent_dir, "requirements.txt")
        if not os.path.isfile(requirements_path):
            print(f"Error: requirements.txt not found in {agent_dir}", file=sys.stderr)
            sys.exit(1)
        # kinnoo.yaml already checked above

        print(f"[kinnoo pack] Packaging agent directory: {agent_dir}")

        # --- Task26: Build wheel files for dependencies ---
        from kinnoo.pack_command import build_wheels, WheelBuildError
        import tempfile
        import zipfile
        wheels_dir = tempfile.TemporaryDirectory(prefix="kinnoo_wheels_")
        try:
            wheel_files = build_wheels(Path(requirements_path), Path(wheels_dir.name))
        except WheelBuildError as e:
            print(f"Error: {e}", file=sys.stderr)
            wheels_dir.cleanup()
            sys.exit(1)

        # --- Task27: Create .kno archive with all contents ---
        archive_name = os.path.basename(abs_agent_dir.rstrip(os.sep)) + ".kno"
        archive_path = os.path.join(os.path.dirname(abs_agent_dir), archive_name)
        with zipfile.ZipFile(archive_path, "w", zipfile.ZIP_DEFLATED) as z:
            # Add kinnoo.yaml
            z.write(kinnoo_yaml_path, arcname="kinnoo.yaml")
            # Add entrypoint
            z.write(entrypoint_path, arcname=os.path.basename(entrypoint_path))
            # Add requirements.txt
            z.write(requirements_path, arcname="requirements.txt")
            # Add wheel files
            for wf in wheel_files:
                z.write(wf, arcname=f"wheels/{os.path.basename(wf)}")
        print(f"[kinnoo pack] Archive created: {archive_path}")
        wheels_dir.cleanup()
        return

if __name__ == "__main__":
    main()
