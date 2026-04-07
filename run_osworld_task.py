#!/usr/bin/env python3
"""
Run a single OSWorld multi_apps task with GUI Agent Harness.

Usage:
    python3 run_osworld_task.py 44                    # task number (1-indexed)
    python3 run_osworld_task.py 44 --vm 172.16.82.132  # custom VM IP
    python3 run_osworld_task.py 44 --max-steps 20      # custom max steps
    python3 run_osworld_task.py 44 --no-setup           # skip VM reset + file download
"""

import argparse
import glob
import json
import os
import subprocess
import sys
import time
import urllib.request

OSWORLD_DIR = os.path.expanduser("~/OSWorld")
VM_PORT = 5000
VMRUN = "/Applications/VMware Fusion.app/Contents/Public/vmrun"
VMX = os.path.expanduser("~/OSWorld/vmware_vm_data/Ubuntu-arm/Ubuntu.vmx")


def get_task_config(task_num: int) -> dict:
    """Load task config from OSWorld evaluation_examples."""
    test_all = json.load(open(os.path.join(OSWORLD_DIR, "evaluation_examples/test_all.json")))
    task_ids = test_all.get("multi_apps", [])
    if task_num < 1 or task_num > len(task_ids):
        raise ValueError(f"Task {task_num} out of range (1-{len(task_ids)})")

    tid = task_ids[task_num - 1]
    files = glob.glob(os.path.join(OSWORLD_DIR, f"evaluation_examples/examples/multi_apps/{tid}*.json"))
    if not files:
        raise FileNotFoundError(f"Task config not found for {tid}")

    config = json.load(open(files[0]))
    config["_task_num"] = task_num
    return config


def setup_vm(vm_ip: str, task_config: dict):
    """Revert VM to snapshot and download task files."""
    print(f"Reverting VM to init_state...")
    subprocess.run([VMRUN, "revertToSnapshot", VMX, "init_state"],
                   capture_output=True, timeout=60)
    subprocess.run([VMRUN, "start", VMX, "nogui"],
                   capture_output=True, timeout=60)

    # Wait for VM API
    vm_url = f"http://{vm_ip}:{VM_PORT}"
    print(f"Waiting for VM at {vm_url}...")
    for i in range(30):
        try:
            urllib.request.urlopen(f"{vm_url}/screenshot", timeout=5)
            break
        except Exception:
            time.sleep(3)

    # Execute config commands + download files
    cmds = []
    for c in task_config["config"]:
        if c["type"] == "command":
            cmds.append(" ".join(c["parameters"]["command"]))
        elif c["type"] == "download":
            for f in c["parameters"]["files"]:
                cmds.append(f'curl -sL -o "{f["path"]}" "{f["url"]}"')

    if cmds:
        full_cmd = " && ".join(cmds) + " && echo SETUP_DONE"
        payload = json.dumps({"command": full_cmd, "shell": True}).encode()
        req = urllib.request.Request(
            f"{vm_url}/execute",
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=180).read())
        if "SETUP_DONE" in resp.get("output", ""):
            print("VM setup complete.")
        else:
            print(f"WARNING: Setup may have failed: {resp.get('output', '')[:100]}")


def run_task(task_config: dict, vm_ip: str, max_steps: int) -> dict:
    """Run the task using execute_task."""
    os.environ["NO_PROXY"] = f"{vm_ip}/24"
    os.environ["no_proxy"] = f"{vm_ip}/24"

    # Kill stale processes
    subprocess.run(["pkill", "-f", "claude.*stream-json"], capture_output=True)
    time.sleep(1)

    from gui_harness.adapters.vm_adapter import patch_for_vm
    patch_for_vm(f"http://{vm_ip}:{VM_PORT}")

    from gui_harness.tasks.execute_task import execute_task
    from gui_harness.runtime import GUIRuntime

    runtime = GUIRuntime(provider="claude-code", model="sonnet")

    app_name = task_config.get("related_apps", ["desktop"])[0]
    result = execute_task(
        task=task_config["instruction"],
        runtime=runtime,
        max_steps=max_steps,
        app_name=app_name,
    )
    return result


def print_result(result: dict, task_num: int):
    """Print task result summary."""
    print()
    print("=" * 60)
    print(f"Task {task_num}: {'SUCCESS' if result['success'] else 'FAILED'}")
    print(f"Steps: {result['steps_taken']} | Total: {result.get('total_time', '?')}s")
    print()
    for h in result["history"]:
        status = "OK" if h.get("success") else "FAIL"
        timing = h.get("timing", {})
        step_t = timing.get("step_total", "?")
        output = str(h.get("output", ""))[:120]
        print(f"  {h['step']:2d}. [{status}] {h['action']:15s} ({step_t}s)")
        if output.strip():
            print(f"      output: {output}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Run OSWorld multi_apps task")
    parser.add_argument("task_num", type=int, help="Task number (1-indexed)")
    parser.add_argument("--vm", default="172.16.82.132", help="VM IP address")
    parser.add_argument("--max-steps", type=int, default=15, help="Max steps")
    parser.add_argument("--no-setup", action="store_true", help="Skip VM reset")
    args = parser.parse_args()

    task_config = get_task_config(args.task_num)
    task_id = task_config["id"][:8]
    print(f"Task {args.task_num} ({task_id}): {task_config['instruction'][:80]}...")
    print(f"Apps: {task_config.get('related_apps')} | Proxy: {task_config.get('proxy')}")

    if task_config.get("proxy"):
        print("WARNING: This task requires proxy/internet access.")

    if not args.no_setup:
        setup_vm(args.vm, task_config)

    result = run_task(task_config, args.vm, args.max_steps)
    print_result(result, args.task_num)

    # Clean up
    subprocess.run(["pkill", "-f", "claude.*stream-json"], capture_output=True)


if __name__ == "__main__":
    main()
