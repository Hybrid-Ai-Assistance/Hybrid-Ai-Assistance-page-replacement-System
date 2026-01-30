# Hybrid AI-Assisted Page Replacement System 🧠

<p align="center">
  <img src="https://img.shields.io/badge/Linux_Kernel-Research-blue" alt="Linux Kernel">
  <img src="https://img.shields.io/badge/AI-ML_Advisory-brightgreen" alt="AI/ML">
  <img src="https://img.shields.io/badge/Memory_Management-Advanced-yellow" alt="Memory Management">
  <img src="https://img.shields.io/badge/Status-Research_Project-orange" alt="Status">
</p>

## 📋 Overview

**Hybrid AI-Assisted Page Replacement System** is a research project that enhances Linux memory management using predictive AI. Instead of replacing traditional algorithms (like [LRU](https://en.wikipedia.org/wiki/Cache_replacement_policies#Least_recently_used_(LRU)) or [CLOCK](https://en.wikipedia.org/wiki/Page_replacement_algorithm#Clock)), we add an **intelligent advisory layer** that predicts major page faults before they happen.

> 🎯 **Goal**: Make page replacement *future-aware*, not just history-dependent.

## 🚀 Quick Start

```bash
# Clone the repository
git clone https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System.git
cd Hybrid-Ai-Assistance-page-replacement-System

# Install dependencies
pip install -r requirements.txt

# Explore kernel module
cd kernel_module
make
sudo insmod pfn_tracker.ko
```

## 📊 How It Works

### Traditional Approach (Reactive)
Traditional systems wait for page faults, then react:
```
Page Fault → Disk I/O → Load Page → Continue
       ⬇
High Latency (100-1000x slower)
```

### Our Approach (Predictive)
We predict faults *before* they occur:
```
PFN Pattern Analysis → AI Prediction → Advisory Signal → Smarter Eviction
       ⬇
Avoid unnecessary disk I/O
```

## 🏗️ System Architecture

```
    Linux Kernel
         ↓
   Kprobe Hooks
         ↓
PFN Data Capture
         ↓
Per-Process Sequence Builder
         ↓
   GRU Prediction Model
         ↓
  Advisory Signals
         ↓
 Victim Validation
         ↓
Reduced Major Faults
```

## 🧩 Team Roles and Responsibilities

| Role | Directory | Responsibility |
|------|------------|----------------|
| AI Developer | `linux_and_ai_design/ai_module/` | Develop predictive AI models for page replacement |
| Linux Expert | `linux_and_ai_design/linux_module/` | Integrate AI model insights into Linux-level simulation |
| Fullstack / Software Designer | `software_design/` | Develop the main system interface, backend logic |
| Frontend Developer | `software_design/frontend/` | UI for visualizing memory and AI performance |
| Backend Developer | `software_design/backend/` | APIs, model connection, and DB integration |
| Web Designer | `web_platform/` | Develop global web access for this service |
| Documentation Team | `docs/` | Maintain project documentation, architecture, and reports |

## ⚙️ Tech Stack

| Component | Technology |
|-----------|------------|
| **AI/ML** | Python, PyTorch/TensorFlow, Scikit-learn |
| **Linux Kernel** | C, Shell scripting, Kprobes |
| **Backend** | Flask/Node.js, REST APIs, Database |
| **Frontend** | React, HTML5, CSS3, JavaScript |
| **Web Platform** | Next.js, Express |
| **Version Control** | GitHub, Git |
| **Data Processing** | Pandas, NumPy, Custom pipelines |

## 🛠️ Key Components

### 1. **Kernel Instrumentation**
- Uses [kprobes](https://www.kernel.org/doc/Documentation/kprobes.txt) for safe runtime hooking
- Captures: `do_swap_page()`, `finish_fault()`, `shrink_folio_list()`
- Tracks: Virtual Address → PFN mappings, process context, timing data

### 2. **AI Prediction Engine (GRU V3)**
- **Model**: [Gated Recurrent Unit](https://en.wikipedia.org/wiki/Gated_recurrent_unit) (lightweight alternative to LSTM)
- **Input**: 30-step PFN sequence window
- **Output**: Predicted future PFNs + confidence scores
- **Why GRU?**: Better temporal pattern capture with lower overhead

### 3. **Hybrid Advisory Layer**
- **Does NOT override** kernel decisions
- Provides **recommendation signals** only
- Validates victim selection
- Maintains kernel safety and compatibility

## 📈 Performance Benefits

| Metric | Before | After (Expected) |
|--------|--------|------------------|
| Major Faults | High | **Reduced 30-50%** |
| Disk I/O | Frequent | **Less frequent** |
| Response Time | Variable | **More stable** |
| Memory Thrashing | Possible | **Mitigated** |

## 🧪 Research Context

This project addresses a fundamental OS challenge: **Major Page Faults** are expensive because they require disk access (mechanical latency). Our system learns application memory patterns to avoid evicting pages that will soon be needed.

**Learn more about:**
- [Virtual Memory](https://en.wikipedia.org/wiki/Virtual_memory) - How OS manages memory abstraction
- [Page Replacement Algorithms](https://en.wikipedia.org/wiki/Page_replacement_algorithm) - Traditional approaches
- [Locality of Reference](https://en.wikipedia.org/wiki/Locality_of_reference) - Why patterns exist in memory access
- [Major vs Minor Faults](https://www.geeksforgeeks.org/page-fault-handling-in-operating-system/) - Understanding the cost difference

## 📁 Project Structure

```
├── linux_and_ai_design/          # Core AI+Linux integration
│   ├── ai_module/                # AI Developer: Prediction models
│   │   ├── gru_v3.py            # GRU model implementation
│   │   ├── training/            # Training scripts
│   │   └── prediction_service.py # Real-time prediction
│   └── linux_module/            # Linux Expert: Kernel integration
│       ├── kernel_hooks/        # Kprobe implementations
│       ├── pfn_tracker/         # PFN data collection
│       └── advisory_interface/  # Kernel advisory signals
├── software_design/              # Main application
│   ├── frontend/                # Frontend Developer: UI components
│   │   ├── src/components/      # React components
│   │   ├── public/              # Static assets
│   │   └── package.json         # Frontend dependencies
│   └── backend/                 # Backend Developer: API services
│       ├── api/                 # REST endpoints
│       ├── database/            # Data persistence
│       └── services/            # Business logic
├── web_platform/                 # Web Designer: Global access
│   ├── next_app/                # Next.js application
│   └── api_gateway/             # Express API gateway
├── kernel_module/               # Low-level kernel components
├── evaluation/                  # Performance testing
├── docs/                        # Documentation Team
│   ├── architecture.md          # System design
│   ├── api_docs.md             # API documentation
│   └── user_guide.md           # User instructions
└── requirements.txt             # Python dependencies
```

## 🔍 Detailed Workflow

### Step 1: Data Collection
```python
# Kernel captures when major fault occurs
Major Fault at VA: 0x7f8a1b402000
→ Resolved to PFN: 0x12345
→ Process: chrome (PID: 4512)
→ Timestamp: 164879.512 ms
```

### Step 2: Sequence Building
```
Chrome Process PFN Sequence:
[0x12340, 0x12341, 0x12342, 0x12345, ...]
Window: 30 steps → Next: 0x12346 (predicted)
```

### Step 3: AI Prediction
```python
# GRU analyzes temporal patterns
model = GRU(input_size=256, hidden_size=512)
predicted_pfns = model(pfn_sequence)
confidence = calculate_confidence(predicted_pfns)
```

### Step 4: Advisory Signal
```
Advisory: "PFN 0x12346 likely needed soon"
→ Kernel: "Avoid evicting PFN 0x12346"
→ Result: Prevents future fault
```

## 🎓 Academic Background

**Final Year Research Project (2025-2026)**  
Department of Computer Science & Engineering

### Supervised By:
- **Mr. R. S. Sharma** - Head of Department
- **Ms. Mithilesh Sharma** - Faculty, CS Department

### Research Team:
| Name | ID |
|------|----|
| Hemant Singh Chouhan | 22/420 | 
| Naresh Parmar | 22/519 |
| Naman Sehra | 22/518 | 
| Shubham Garg | 23/776 | 

## 🚀 How to Contribute

### Role-Based Contribution Workflow

1. **Clone the repository**
   ```bash
   git clone https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System.git
   ```

2. **Checkout your role-specific branch**
   ```bash
   # AI Developers
   git checkout ai-dev
   
   # Linux Experts
   git checkout linux-dev
   
   # Frontend Developers
   git checkout frontend-dev
   
   # Backend Developers
   git checkout backend-dev
   
   # Web Designers
   git checkout web-dev
   ```

3. **Work inside your designated directory only**
   - AI Developers: `linux_and_ai_design/ai_module/`
   - Linux Experts: `linux_and_ai_design/linux_module/`
   - Frontend Developers: `software_design/frontend/`
   - Backend Developers: `software_design/backend/`
   - Web Designers: `web_platform/`
   - Documentation: `docs/`

4. **Commit and push your changes**
   ```bash
   git add .
   git commit -m "Description of changes"
   git push origin your-branch-name
   ```

5. **Create a Pull Request for review**
   - Navigate to GitHub repository
   - Click "New Pull Request"
   - Select appropriate reviewers
   - Add detailed description

### Contribution Guidelines
- Follow the **directory structure** strictly
- Maintain **code quality** and documentation
- Test your changes **before committing**
- Coordinate with **other role teams** for integration
- Update documentation when adding new features

## 📚 Learning Resources

### Prerequisites (Recommended Reading)
1. **Memory Management Basics**
   - [Virtual Memory Explained](https://www.techtarget.com/searchstorage/definition/virtual-memory)
   - [Page Tables and MMU](https://en.wikipedia.org/wiki/Memory_management_unit)

2. **Page Replacement Algorithms**
   - [LRU Algorithm](https://www.geeksforgeeks.org/program-for-least-recently-used-lru-page-replacement-algorithm/)
   - [CLOCK Algorithm](https://www.geeksforgeeks.org/clock-page-replacement-algorithm/)
   - [FIFO vs Optimal](https://www.javatpoint.com/os-page-replacement-algorithms)

3. **Linux Kernel Internals**
   - [Kernel Memory Management](https://www.kernel.org/doc/html/latest/admin-guide/mm/)
   - [Kprobes Documentation](https://docs.kernel.org/trace/kprobes.html)

4. **Machine Learning for Systems**
   - [Sequence Models (RNN/LSTM/GRU)](https://www.coursera.org/lecture/nlp-sequence-models/recurrent-neural-network-model-ftkzt)
   - [Temporal Pattern Recognition](https://en.wikipedia.org/wiki/Time_series)

## 🚧 Installation & Setup

### Requirements
- Linux Kernel 5.4+
- Python 3.8+
- PyTorch 1.9+
- Node.js 16+ (for frontend/web)
- Kernel headers for compilation

### Step-by-Step Setup
```bash
# 1. Clone and setup
git clone https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System.git
cd Hybrid-Ai-Assistance-page-replacement-System

# 2. Install Python dependencies (AI/Backend)
pip install -r requirements.txt

# 3. Install Node dependencies (Frontend/Web)
cd software_design/frontend && npm install
cd ../../web_platform && npm install

# 4. Build kernel module (Linux Experts)
cd ../linux_and_ai_design/linux_module/kernel_hooks
make
sudo insmod pfn_tracker.ko

# 5. Verify installation
dmesg | grep "PFN Tracker"  # Should show module loaded

# 6. Start services
# Start AI prediction service
python linux_and_ai_design/ai_module/prediction_service.py

# Start backend API
cd software_design/backend && python app.py

# Start frontend
cd ../frontend && npm start

# Start web platform
cd ../../web_platform && npm run dev
```

## 📊 Evaluation & Results

### Test Workloads
We evaluate using:
- **Memory-intensive applications** (Chrome, MATLAB, VMs)
- **Database workloads** (MySQL, PostgreSQL)
- **Scientific computing** (TensorFlow, NumPy)
- **Gaming applications** (Unity, Unreal Engine)

### Key Metrics
- **Major Fault Reduction Rate**: Target 30-50% improvement
- **Prediction Accuracy**: PFN sequence forecasting precision
- **System Overhead**: <5% CPU, <2% memory impact
- **Latency Improvement**: Reduced 95th percentile response times

## 🔮 Future Work

1. **Real-time Kernel Integration**
   - Move from userspace to kernelspace advisory
   - Direct integration with mm_struct

2. **Advanced Models**
   - Transformer-based sequence prediction
   - Multi-process correlation learning
   - Cross-application pattern transfer

3. **Production Features**
   - Self-tuning hyperparameters
   - Workload classification
   - Energy-aware predictions

4. **Extended Research**
   - [NUMA](https://en.wikipedia.org/wiki/Non-uniform_memory_access) optimization
   - [Huge Pages](https://www.kernel.org/doc/html/latest/admin-guide/mm/hugetlbpage.html) prediction
   - [Memory Compression](https://www.kernel.org/doc/html/latest/admin-guide/mm/ksm.html) integration

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 📞 Contact & Support

- **GitHub Issues**: [Report bugs or request features](https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System/issues)
- **Role-specific Discussions**: Check respective directory README files
- **Academic Inquiries**: Contact via university department

## 🙏 Acknowledgments

- Our faculty supervisors for guidance and support
- Linux kernel community for excellent documentation
- Open source ML community for foundational tools
- Previous research in predictive memory systems
- All contributors maintaining their respective modules

---

<p align="center">
  <em>"Predicting the future of memory, one page at a time."</em>
</p>

<p align="center">
  <a href="https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System/stargazers">
    <img src="https://img.shields.io/github/stars/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System" alt="GitHub Stars">
  </a>
  <a href="https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System/network/members">
    <img src="https://img.shields.io/github/forks/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System" alt="GitHub Forks">
  </a>
  <a href="https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System/issues">
    <img src="https://img.shields.io/github/issues/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System" alt="GitHub Issues">
  </a>
  <a href="https://github.com/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System/blob/main/LICENSE">
    <img src="https://img.shields.io/github/license/Hybrid-Ai-Assistance/Hybrid-Ai-Assistance-page-replacement-System" alt="License">
  </a>
</p>
