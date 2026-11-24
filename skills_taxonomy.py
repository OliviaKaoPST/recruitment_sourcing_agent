"""Skill taxonomy: canonical skill -> aliases (EN + 繁中). Extend freely."""

TAXONOMY = {
    "cuda": ["cuda", "cuda c++", "gpgpu", "nvcc"],
    "c++": ["c++", "cpp", "c/c++", "modern c++"],
    "python": ["python", "python3"],
    "pytorch": ["pytorch", "torch"],
    "tensorrt": ["tensorrt", "trt"],
    "triton": ["triton inference server", "openai triton", "triton kernel"],
    "llm": ["llm", "large language model", "大型語言模型", "transformer", "gpt"],
    "deep learning": ["deep learning", "深度學習", "neural network"],
    "gpu architecture": ["gpu architecture", "gpu", "shader", "sm occupancy", "圖形處理器"],
    "rtl design": ["rtl", "verilog", "systemverilog", "vhdl"],
    "design verification": ["uvm", "design verification", "dv engineer", "testbench", "驗證"],
    "asic": ["asic", "soc design", "tape-out", "tapeout", "流片"],
    "fpga": ["fpga", "vivado", "quartus"],
    "physical design": ["physical design", "pnr", "place and route", "innovus", "icc2", "實體設計"],
    "dft": ["dft", "design for test", "scan insertion", "atpg"],
    "firmware": ["firmware", "bootloader", "韌體"],
    "linux kernel": ["linux kernel", "kernel driver", "device driver", "驅動程式"],
    "embedded": ["embedded", "rtos", "bare metal", "嵌入式"],
    "networking": ["infiniband", "rdma", "roce", "nccl", "高速網路"],
    "pcie": ["pcie", "pci express", "nvlink"],
    "memory": ["hbm", "ddr5", "gddr", "lpddr"],
    "kubernetes": ["kubernetes", "k8s", "helm"],
    "docker": ["docker", "container"],
    "ci/cd": ["ci/cd", "jenkins", "github actions", "gitlab ci"],
    "hpc": ["hpc", "mpi", "slurm", "supercomputing", "高效能運算"],
    "autonomous vehicles": ["autonomous driving", "adas", "自駕"],
    "robotics": ["robotics", "ros", "isaac sim", "機器人"],
}

# Role family -> default must-have / nice-to-have (used by boolean_builder when no JD given)
ROLE_PRESETS = {
    "cuda_engineer": {
        "must": ["cuda", "c++", "gpu architecture"],
        "nice": ["python", "pytorch", "tensorrt", "hpc", "llm"],
    },
    "asic_dv": {
        "must": ["design verification", "rtl design"],
        "nice": ["asic", "python", "pcie", "memory"],
    },
    "driver_firmware": {
        "must": ["linux kernel", "c++"],
        "nice": ["firmware", "pcie", "embedded"],
    },
    "ai_infra": {
        "must": ["python", "kubernetes"],
        "nice": ["pytorch", "llm", "hpc", "networking", "docker"],
    },
}
