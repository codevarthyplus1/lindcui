# KVM Source Code Documentation
# Complete File-by-File Reference

**Document Version:** 1.0
**Linux Kernel Version:** 6.13-rc (Latest)
**Last Updated:** 2025-11-15

---

## Table of Contents

1. [Introduction](#introduction)
2. [KVM Architecture Overview](#kvm-architecture-overview)
3. [Core KVM Files (virt/kvm/)](#core-kvm-files-virtkvm)
4. [x86 Architecture Files (arch/x86/kvm/)](#x86-architecture-files-archx86kvm)
5. [Memory Management Unit (arch/x86/kvm/mmu/)](#memory-management-unit-archx86kvmmmu)
6. [Intel VMX Implementation (arch/x86/kvm/vmx/)](#intel-vmx-implementation-archx86kvmvmx)
7. [AMD SVM Implementation (arch/x86/kvm/svm/)](#amd-svm-implementation-archx86kvmsvm)
8. [Header Files and APIs](#header-files-and-apis)

---

## Introduction

**KVM (Kernel-based Virtual Machine)** is a Linux kernel module that transforms the Linux kernel into a bare-metal hypervisor. It leverages hardware virtualization extensions to provide near-native performance for virtual machines.

### Key Concepts

- **Type-1 Hypervisor**: KVM turns Linux into a native hypervisor
- **Hardware Acceleration**: Uses Intel VT-x (VMX) or AMD-V (SVM)
- **Full Virtualization**: Guests run unmodified operating systems
- **Memory Management**: Extended Page Tables (EPT) / Nested Page Tables (NPT)
- **Device Emulation**: Works with QEMU for I/O device emulation

### Architecture Components

```
┌─────────────────────────────────────────────────────┐
│              User Space (QEMU/libvirt)              │
├─────────────────────────────────────────────────────┤
│                   /dev/kvm ioctl                    │
├─────────────────────────────────────────────────────┤
│         KVM Core (virt/kvm/)                        │
│  - VM Management                                     │
│  - vCPU Scheduling                                   │
│  - Device Emulation Framework                        │
├─────────────────────────────────────────────────────┤
│      Architecture-Specific (arch/x86/kvm/)          │
│  ┌──────────────┐  ┌──────────────┐                │
│  │  Intel VMX   │  │   AMD SVM    │                │
│  │   (vmx/)     │  │   (svm/)     │                │
│  └──────────────┘  └──────────────┘                │
│         Memory Management (mmu/)                    │
├─────────────────────────────────────────────────────┤
│              Hardware (CPU with VT-x/AMD-V)         │
└─────────────────────────────────────────────────────┘
```

---

## Core KVM Files (virt/kvm/)

This directory contains the architecture-independent core of KVM. These files implement the fundamental virtualization infrastructure shared across all CPU architectures (x86, ARM, RISC-V, etc.).

### kvm_main.c (170,748 bytes)

**Purpose**: Core KVM hypervisor implementation and main entry point

**Key Responsibilities**:
- **VM Lifecycle Management**: Creating, destroying, and managing virtual machines
- **vCPU Management**: Virtual CPU allocation, scheduling, and state management
- **Memory Management**: Guest physical memory allocation and mapping
- **Device Interface**: `/dev/kvm` character device implementation
- **IOCTL Handler**: Main ioctl interface for userspace (QEMU) communication
- **VCPU Run Loop**: Executes guest code and handles VM exits
- **Event Handling**: IRQ injection, timers, and asynchronous events
- **Statistics and Debugging**: Performance counters and debugging infrastructure

**Key Functions**:
- `kvm_init()`: Initialize KVM subsystem
- `kvm_create_vm()`: Create a new virtual machine
- `kvm_vcpu_ioctl()`: Handle vCPU-specific operations
- `kvm_vcpu_run()`: Main execution loop for running guest code
- `kvm_set_memory_region()`: Configure guest memory regions
- `kvm_irq_delivery()`: Deliver interrupts to guest

**This is the heart of KVM** - it provides the core virtualization framework.

---

### async_pf.c / async_pf.h (6,335 + 518 bytes)

**Purpose**: Asynchronous Page Fault handling

**Key Responsibilities**:
- **Non-Blocking Page Faults**: Handle guest page faults without blocking vCPU
- **Guest Memory Access**: Asynchronous loading of swapped-out guest pages
- **Performance Optimization**: Avoid vCPU pause during page-in operations
- **Notification Mechanism**: Notify guest when page is available

**How It Works**:
1. Guest accesses swapped-out page → VM exit
2. KVM marks page fault as async and returns to guest
3. Guest continues execution (if possible)
4. When page ready, KVM injects async PF completion event
5. Guest handles page and retries access

**Use Case**: Improves performance when guest memory is overcommitted

---

### binary_stats.c (4,605 bytes)

**Purpose**: Binary statistics interface for KVM

**Key Responsibilities**:
- **Performance Metrics**: Expose KVM statistics in binary format
- **Efficient Data Export**: Low-overhead stats collection
- **Monitoring Interface**: Used by tools like `kvm_stat`
- **Per-VM and Per-vCPU Stats**: Detailed performance counters

**Metrics Tracked**:
- VM exits (by reason)
- Instruction emulation count
- Page fault statistics
- Interrupt injection counts
- Hypercall statistics

---

### coalesced_mmio.c / coalesced_mmio.h (4,720 + 884 bytes)

**Purpose**: Coalesced Memory-Mapped I/O optimization

**Key Responsibilities**:
- **Batched MMIO Writes**: Combine multiple MMIO writes into single operations
- **VM Exit Reduction**: Reduces costly VM exits for MMIO operations
- **Ring Buffer**: Stores pending MMIO writes in circular buffer
- **Flush Mechanism**: Periodic flushing to actual devices

**Example Use Case**:
- Guest writes to video framebuffer (thousands of writes)
- Without coalescing: Each write causes VM exit (slow)
- With coalescing: Writes buffered, flushed in batch (fast)

**Performance Impact**: Can reduce VM exits by 90%+ for MMIO-heavy workloads

---

### dirty_ring.c (7,312 bytes)

**Purpose**: Dirty page tracking using ring buffer

**Key Responsibilities**:
- **Live Migration**: Track which guest memory pages were modified
- **Ring Buffer Approach**: Efficient dirty page logging using per-vCPU rings
- **Scalability**: Better than bitmap approach for large VMs
- **Pause-less Tracking**: Guest can continue while userspace collects dirty pages

**Dirty Ring vs. Dirty Bitmap**:
- **Old method (bitmap)**: Global bitmap of dirty pages, lock contention
- **New method (ring)**: Per-vCPU lock-free rings, better scalability

**Use Case**: Live VM migration, incremental backup, memory snapshots

---

### eventfd.c (25,929 bytes)

**Purpose**: Event file descriptor integration for KVM

**Key Responsibilities**:
- **IRQ Forwarding**: Map eventfd events to guest interrupts (irqfd)
- **Guest Notifications**: Guest-to-host notification mechanism (ioeventfd)
- **Device Assignment**: Used for VFIO device passthrough
- **Fast I/O Path**: Bypass QEMU for high-performance I/O

**Two Main Features**:

1. **irqfd**: Host eventfd → Guest IRQ
   - Device writes to eventfd → KVM injects IRQ to guest
   - Used for: virtio, VFIO device interrupts

2. **ioeventfd**: Guest MMIO write → Host eventfd
   - Guest writes to specific address → eventfd signaled
   - Userspace (QEMU) handles without VM exit
   - Used for: virtio kick, device notifications

**Performance**: Critical for high-speed I/O (network, storage)

---

### guest_memfd.c (20,699 bytes)

**Purpose**: Guest memory file descriptor for confidential computing

**Key Responsibilities**:
- **Private Guest Memory**: Memory inaccessible to host
- **TDX/SEV Support**: Enables confidential computing
- **Encrypted Memory**: Guest memory encrypted with CPU keys
- **Isolation**: Protect guest from compromised hypervisor

**Confidential Computing**:
- **Intel TDX (Trust Domain Extensions)**: Hardware-encrypted VMs
- **AMD SEV (Secure Encrypted Virtualization)**: Memory encryption
- Guest memory hidden from host OS and hypervisor

**Use Case**: Running sensitive workloads in untrusted cloud environments

---

### irqchip.c (6,220 bytes)

**Purpose**: Interrupt controller chip emulation framework

**Key Responsibilities**:
- **In-Kernel IRQ Handling**: Emulate interrupt controllers in kernel space
- **IRQ Routing**: Route interrupts to correct vCPU
- **Performance**: Avoid userspace (QEMU) for interrupt delivery
- **Architecture Abstraction**: Common interface for different IRQ chips

**Supported IRQ Controllers**:
- **x86**: IOAPIC, LAPIC (Local APIC), PIC (8259)
- **ARM**: GIC (Generic Interrupt Controller)
- **RISC-V**: PLIC, APLIC

**Why In-Kernel?**: Interrupt delivery is latency-critical; kernel-space handling is 10x faster

---

### pfncache.c (12,125 bytes)

**Purpose**: Page Frame Number caching

**Key Responsibilities**:
- **Fast Guest Memory Access**: Cache frequently accessed guest memory mappings
- **Translation Cache**: Cache GPA (Guest Physical) → HPA (Host Physical) mappings
- **Reduce TLB Misses**: Avoid repeated page table walks
- **Paravirtualization Support**: Used for paravirt structures (e.g., steal time)

**Example**:
- Guest exposes shared memory structure (like vcpu_runstate)
- KVM caches the HPA mapping
- Fast access without page table walks on each read/write

---

### vfio.c / vfio.h (7,820 + 289 bytes)

**Purpose**: VFIO (Virtual Function I/O) integration

**Key Responsibilities**:
- **Device Passthrough**: Pass physical PCI devices directly to guest
- **IOMMU Support**: Secure device access via IOMMU
- **Interrupt Handling**: Forward device interrupts to guest
- **DMA Remapping**: Allow device DMA to guest memory

**VFIO Architecture**:
```
Guest Driver → VFIO Device → IOMMU → Physical Device
```

**Use Cases**:
- GPU passthrough for gaming/ML
- Network card passthrough for high performance
- Storage controller passthrough

**Security**: IOMMU ensures device can only access guest memory, not host

---

### Kconfig (2,643 bytes)

**Purpose**: KVM kernel configuration options

**Key Options**:
- `CONFIG_KVM`: Enable KVM support
- `CONFIG_KVM_INTEL`: Intel VT-x support
- `CONFIG_KVM_AMD`: AMD-V support
- `CONFIG_KVM_MMU_AUDIT`: MMU debugging
- Dependencies and feature flags

---

### Makefile.kvm (540 bytes)

**Purpose**: Build system for KVM core modules

**Builds**:
- Core KVM object files
- Conditional compilation based on config
- Links architecture-independent KVM code

---

## x86 Architecture Files (arch/x86/kvm/)

This directory contains x86-specific KVM implementation. It handles Intel and AMD CPU virtualization features, instruction emulation, interrupt controllers, and platform-specific optimizations.

---

### x86.c (396,081 bytes)

**Purpose**: Main x86 KVM implementation - the largest and most complex file

**Key Responsibilities**:
- **vCPU Emulation**: Emulate x86 CPU behavior
- **Register Management**: Handle guest CPU registers (GPRs, control, MSRs)
- **CPUID Handling**: Virtualize CPUID instruction for guest CPU detection
- **MSR Access**: Model-Specific Register read/write emulation
- **VM Exit Handling**: Process exits from guest to hypervisor
- **FPU/SIMD**: x87, SSE, AVX state management
- **Time Management**: TSC (Time Stamp Counter), APIC timer virtualization
- **Nested Virtualization**: Run hypervisor inside VM (L1, L2 guests)
- **Paravirtualization**: KVM paravirt features (steal time, async PF)

**Critical Functions**:
- `kvm_arch_vcpu_ioctl_run()`: Main x86 vCPU execution loop
- `vcpu_enter_guest()`: Enter guest mode
- `handle_exit()`: Dispatch VM exit handlers
- `kvm_emulate_cpuid()`: CPUID virtualization
- `kvm_set_msr()` / `kvm_get_msr()`: MSR access
- `kvm_arch_vcpu_create()`: Initialize x86 vCPU

**This is the second most important file** after kvm_main.c for x86 virtualization

---

### x86.h (22,495 bytes)

**Purpose**: Main x86 KVM header file

**Contents**:
- Function prototypes for x86.c
- x86-specific data structures
- Inline helper functions
- Common definitions

---

### cpuid.c / cpuid.h (56,385 + 8,703 bytes)

**Purpose**: CPUID virtualization and guest CPU feature exposure

**Key Responsibilities**:
- **Feature Filtering**: Hide/expose CPU features to guest
- **CPUID Emulation**: Virtualize CPUID instruction
- **CPU Model Spoofing**: Present specific CPU model to guest
- **Security**: Hide host CPU vulnerabilities from guest
- **Migration**: Ensure CPU compatibility across hosts

**CPUID Leaves Handled**:
- `0x00`: Vendor string (GenuineIntel, AuthenticAMD)
- `0x01`: CPU features (SSE, AVX, VMX)
- `0x07`: Extended features (AVX-512, SHA, FSGSBASE)
- `0x0A`: Architectural performance monitoring
- `0x0D`: XSAVE features
- `0x40000000+`: Hypervisor leaves (KVM signature)

**Example**:
```c
Guest executes: CPUID EAX=1
KVM intercepts and returns: Features with VMX bit cleared
Guest sees: Standard CPU, no nested virt capability
```

**Security Implication**: Prevent guest from detecting it runs in VM (or allow if desired)

---

### emulate.c (145,223 bytes)

**Purpose**: x86 instruction emulator - extremely complex

**Key Responsibilities**:
- **Software Emulation**: Emulate x86 instructions that cannot be directly executed
- **Complex Instructions**: Handle MMIO, privileged, or invalid instructions
- **Decode Engine**: Decode x86 instruction encoding (ModR/M, SIB, prefixes)
- **Operand Fetching**: Read/write guest memory and registers
- **String Operations**: MOVS, CMPS, SCAS, etc.
- **Segmentation**: Handle segment overrides and checks

**When is Emulation Needed?**
1. **MMIO Access**: Guest accesses MMIO region → emulate instruction to extract data
2. **Invalid State**: Guest CPU state doesn't allow direct execution
3. **Instruction Intercepts**: Hypervisor wants to intercept specific instructions
4. **Real Mode**: 16-bit real mode requires full emulation

**Example Emulation**:
```
Guest: MOV EAX, [MMIO_ADDRESS]
→ VM Exit
→ KVM decodes instruction
→ KVM reads MMIO_ADDRESS (triggers device)
→ KVM writes result to EAX
→ VM Entry (skip instruction)
```

**Complexity**: Handles 1000+ x86 instruction variants

---

### kvm_emulate.h (18,795 bytes)

**Purpose**: Instruction emulator interface and definitions

**Contents**:
- Emulator callbacks
- Instruction decode structures
- Emulation context
- Operand descriptors

---

### lapic.c / lapic.h (94,530 + 8,135 bytes)

**Purpose**: Local APIC (Advanced Programmable Interrupt Controller) emulation

**Key Responsibilities**:
- **Timer Interrupts**: APIC timer for guest scheduling
- **IPI Delivery**: Inter-Processor Interrupts for SMP guests
- **Interrupt Acceptance**: Receive interrupts from IOAPIC
- **Priority Management**: Interrupt priority and masking
- **x2APIC**: Extended APIC mode for more than 256 CPUs

**LAPIC Components**:
- **APIC Timer**: Programmable timer (one-shot, periodic, TSC-deadline)
- **LVT (Local Vector Table)**: Local interrupt sources
- **ICR (Interrupt Command Register)**: Send IPIs
- **ISR/IRR/TMR**: Interrupt status registers

**Example - APIC Timer**:
```
Guest programs APIC timer: 1ms periodic
→ KVM creates hrtimer (high-resolution timer)
→ After 1ms: hrtimer fires
→ KVM injects APIC timer interrupt to guest
→ Guest handles timer IRQ
```

**Critical for**: SMP, scheduling, timekeeping

---

### ioapic.c / ioapic.h (21,781 + 3,597 bytes)

**Purpose**: I/O APIC (I/O Advanced Programmable Interrupt Controller) emulation

**Key Responsibilities**:
- **External Interrupt Routing**: Route device interrupts to LAPICs
- **IRQ Configuration**: Configure IRQ delivery mode, destination, polarity
- **Redirection Table**: Map GSI (Global System Interrupt) to CPU vectors
- **Interrupt Distribution**: Deliver to single CPU or broadcast

**Routing Example**:
```
PCI Device IRQ 11 → GSI 16
→ IOAPIC Redirection Entry 16: Vector 0x50, CPU 2
→ Delivered to CPU 2, vector 0x50
```

**IOAPIC vs. Legacy PIC**:
- **PIC (8259)**: Old, 15 IRQs max, single CPU
- **IOAPIC**: Modern, 24+ IRQs, multi-CPU delivery

---

### i8254.c / i8254.h (21,037 + 1,856 bytes)

**Purpose**: Intel 8254 Programmable Interval Timer (PIT) emulation

**Key Responsibilities**:
- **Legacy Timer**: Emulate old PC timer chip
- **Periodic Interrupts**: Generate IRQ 0 at programmable frequency
- **System Time**: Used by legacy OSes for timekeeping
- **PC Speaker**: Controls beep sound generation

**Why Still Needed?**
- Legacy OS support (old Linux, Windows)
- BIOS compatibility
- Boot process timing

**Modern Alternative**: HPET (High Precision Event Timer), TSC-deadline APIC timer

---

### i8259.c (14,872 bytes)

**Purpose**: Intel 8259 PIC (Programmable Interrupt Controller) emulation

**Key Responsibilities**:
- **Legacy IRQ Handling**: Emulate old PC interrupt controller
- **15 IRQs**: IRQ 0-15 routing
- **Master/Slave Configuration**: Two cascaded 8259 chips
- **Edge/Level Triggered**: Different interrupt modes

**Why Legacy?**
- BIOS expects it
- Early boot before APIC initialization
- Very old guest OS support

---

### irq.c / irq.h (16,518 + 3,130 bytes)

**Purpose**: x86 IRQ infrastructure and routing

**Key Responsibilities**:
- **IRQ Routing**: Route interrupts from sources to vCPUs
- **IRQ Injection**: Inject interrupts into guest
- **IRQ Ack**: Acknowledge interrupt delivery
- **MSI/MSI-X**: Message Signaled Interrupts for PCI devices

**Interrupt Flow**:
```
Device → IOAPIC/MSI → IRQ Routing → LAPIC → Guest IDT Handler
```

---

### hyperv.c / hyperv.h (78,828 + 10,029 bytes)

**Purpose**: Microsoft Hyper-V paravirtualization interface

**Key Responsibilities**:
- **Hyper-V Enlightenments**: Paravirt features for Windows guests
- **Hypercalls**: Handle Hyper-V-specific hypercalls
- **Synthetic Timers**: Hyper-V timer interface
- **VP Assist Page**: Virtual processor assist page
- **TLB Flush Hypercalls**: Optimized TLB management

**Why Hyper-V in KVM?**
- Windows guests detect Hyper-V and use enlightenments
- Performance boost for Windows VMs (20-50% improvement)
- Compatibility with Windows Server

**Enlightenments**:
- Relaxed timing checks
- Spinlock optimization
- Hypercall-based TLB flush (faster than VM exit)
- Crash dump (blue screen) reporting

---

### xen.c / xen.h (66,353 + 6,973 bytes)

**Purpose**: Xen paravirtualization interface

**Key Responsibilities**:
- **Xen PV Support**: Run Xen paravirtualized guests on KVM
- **Xen Hypercalls**: Emulate Xen hypercall interface
- **Event Channels**: Xen inter-VM communication
- **Shared Info Page**: Xen guest-hypervisor communication page

**Use Case**: Run Xen-optimized Linux distributions on KVM

---

### pmu.c / pmu.h (33,458 + 7,414 bytes)

**Purpose**: Performance Monitoring Unit virtualization

**Key Responsibilities**:
- **Performance Counters**: Virtualize CPU performance counters
- **Profiling Support**: Allow guest to use `perf`, `oprofile`
- **Event Sampling**: PMU event collection in guest
- **vPMU**: Virtual PMU for each vCPU

**Counters Virtualized**:
- Instructions retired
- CPU cycles
- Cache misses (L1, L2, L3)
- Branch mispredictions
- TLB misses

**Use Case**: Profile application performance inside VM

---

### smm.c / smm.h (19,261 + 3,811 bytes)

**Purpose**: System Management Mode emulation

**Key Responsibilities**:
- **SMM Emulation**: Emulate x86 System Management Mode
- **SMRAM**: System Management RAM region
- **SMI Handling**: System Management Interrupt processing
- **Firmware Support**: UEFI/BIOS SMM code execution

**What is SMM?**
- Special CPU mode for low-level system management
- Used by BIOS/UEFI firmware
- Higher privilege than ring 0
- Isolated memory (SMRAM)

**Use Case**: Run UEFI firmware (OVMF) with full SMM support

---

### mtrr.c (2,873 bytes)

**Purpose**: Memory Type Range Register emulation

**Key Responsibilities**:
- **Memory Caching**: Configure memory region caching behavior
- **MTRR Virtualization**: Emulate MTRR MSRs
- **Cache Types**: UC (uncacheable), WB (write-back), WT (write-through), etc.

**Example**:
- Video memory: UC (uncacheable) - direct writes to hardware
- Regular RAM: WB (write-back) - cached for performance

---

### debugfs.c (5,009 bytes)

**Purpose**: DebugFS interface for KVM debugging

**Key Responsibilities**:
- **Debug Information**: Expose KVM state via `/sys/kernel/debug/kvm`
- **Runtime Inspection**: View VCPU state, stats, trace points
- **Development Aid**: Debug VM issues

**Exposed Information**:
- vCPU registers
- Page tables
- IRQ state
- Statistics

---

### fpu.h (4,623 bytes)

**Purpose**: FPU (Floating Point Unit) management

**Contents**:
- FPU state save/restore
- XSAVE/XRSTOR support
- AVX, AVX-512 state management
- Guest FPU context switching

---

### trace.h (49,073 bytes)

**Purpose**: KVM tracepoints for debugging and performance analysis

**Key Responsibilities**:
- **Ftrace Integration**: KVM events for Linux ftrace
- **Performance Analysis**: Trace VM exits, instruction emulation, IRQ injection
- **Debugging**: Understand VM behavior

**Trace Events**:
- `kvm_entry`: Guest entry
- `kvm_exit`: Guest exit (with reason)
- `kvm_msr`: MSR access
- `kvm_mmio`: MMIO access
- `kvm_inj_irq`: Interrupt injection

**Usage**:
```bash
echo 1 > /sys/kernel/debug/tracing/events/kvm/enable
cat /sys/kernel/debug/tracing/trace
```

---

### kvm_cache_regs.h (7,590 bytes)

**Purpose**: Cached guest register access

**Optimization**: Cache frequently accessed guest registers to avoid VMCS reads

---

### kvm_onhyperv.c / kvm_onhyperv.h (3,218 + 1,239 bytes)

**Purpose**: KVM running on Hyper-V (nested virtualization)

**Key Responsibilities**:
- **Nested Hyper-V**: KVM as L1 hypervisor on Hyper-V
- **Enlightenments**: Use Hyper-V features to optimize KVM

---

### reverse_cpuid.h (8,576 bytes)

**Purpose**: Reverse CPUID lookup tables

**Functionality**: Fast lookup from CPU feature to CPUID leaf/bit

---

### tss.h (661 bytes)

**Purpose**: Task State Segment definitions

**Contents**: TSS structure definitions for x86 task switching

---

### kvm-asm-offsets.c (778 bytes)

**Purpose**: Generate assembly offsets for KVM structures

**Usage**: Used by assembly code to access C structure fields

---

### Kconfig (7,482 bytes)

**Purpose**: x86 KVM configuration options

---

### Makefile (1,518 bytes)

**Purpose**: Build x86 KVM modules

---

## Memory Management Unit (arch/x86/kvm/mmu/)

The MMU subsystem is crucial for translating guest virtual addresses to host physical addresses. It implements shadow page tables and Extended Page Tables (EPT).

---

### mmu.c (232,014 bytes)

**Purpose**: KVM Memory Management Unit - the largest MMU file

**Key Responsibilities**:
- **Address Translation**: Guest Virtual → Guest Physical → Host Physical
- **Shadow Page Tables**: Software-based page table virtualization (legacy)
- **EPT/NPT Support**: Hardware-assisted paging (Intel EPT, AMD NPT)
- **Page Fault Handling**: Guest page faults and demand paging
- **TLB Management**: TLB (Translation Lookaside Buffer) invalidation
- **Huge Pages**: 2MB and 1GB page support for performance
- **Dirty Page Tracking**: Track modified pages for live migration
- **Access Tracking**: Track accessed pages

**Address Translation Modes**:

1. **Shadow Paging** (Legacy - no EPT/NPT):
```
Guest VA → Guest Page Tables → Guest PA
         ↓
Shadow Page Tables (maintained by KVM)
         ↓
Host PA
```

2. **EPT/NPT** (Modern - hardware-assisted):
```
Guest VA → Guest Page Tables → Guest PA → EPT/NPT → Host PA
```

**Key Functions**:
- `kvm_mmu_page_fault()`: Handle guest page faults
- `kvm_mmu_load()`: Load MMU context
- `kvm_mmu_invalidate_tlb()`: Invalidate TLB entries
- `kvm_mmu_get_page()`: Allocate shadow page table page

**Performance**: Huge pages improve performance by 20-30%

---

### mmu_internal.h (13,155 bytes)

**Purpose**: Internal MMU data structures and helpers

**Contents**:
- Shadow page structures
- MMU context definitions
- Internal function prototypes

---

### spte.c / spte.h (18,466 + 20,927 bytes)

**Purpose**: Shadow Page Table Entry management

**Key Responsibilities**:
- **SPTE Encoding**: Encode guest page table entries
- **Access Permissions**: Read, write, execute permissions
- **Dirty/Accessed Bits**: Track page modifications
- **MMIO SPTEs**: Special encoding for MMIO regions

**SPTE Bits**:
- Present, writable, user, accessed, dirty
- MMIO, reserved, NX (no-execute)
- AVL bits for KVM metadata

---

### tdp_mmu.c / tdp_mmu.h (62,233 + 3,780 bytes)

**Purpose**: Two-Dimensional Paging MMU (EPT/NPT implementation)

**Key Responsibilities**:
- **EPT Page Tables**: Manage Intel EPT structures
- **NPT Page Tables**: Manage AMD NPT structures
- **Lock-Free Design**: RCU-based concurrent access
- **Scalability**: Better performance for large VMs

**TDP vs. Shadow**:
- **Shadow**: Complex, software page table sync, slow
- **TDP (EPT/NPT)**: Hardware-assisted, fast, simple

**Modern KVM**: Always uses TDP when available (EPT/NPT)

---

### tdp_iter.c / tdp_iter.h (5,168 + 4,574 bytes)

**Purpose**: TDP page table iterator

**Key Responsibilities**:
- **Page Table Walking**: Traverse EPT/NPT page tables
- **Efficient Iteration**: Visit all entries in range
- **Modification Support**: Update entries during iteration

---

### page_track.c / page_track.h (9,501 + 1,963 bytes)

**Purpose**: Guest page access tracking

**Key Responsibilities**:
- **Write Protection**: Track writes to specific guest pages
- **Read Tracking**: Monitor read access (if supported)
- **Dirty Logging**: Efficient dirty page tracking
- **Callbacks**: Notify on page access

**Use Cases**:
- Live migration dirty logging
- Introspection (security monitoring)
- Debugging

---

### paging_tmpl.h (29,543 bytes)

**Purpose**: Paging mode templates

**Key Responsibilities**:
- **Multi-Mode Support**: 32-bit, PAE, 64-bit paging
- **Template Implementation**: Generic code for different paging modes
- **Compile-Time Specialization**: Efficient per-mode implementations

**Paging Modes**:
- 32-bit paging (2-level)
- PAE paging (3-level)
- 64-bit paging (4-level)
- 5-level paging (Intel LA57)

---

### mmutrace.h (10,365 bytes)

**Purpose**: MMU tracepoints

**Trace Events**:
- `kvm_mmu_pagetable_walk`: Page table walk
- `kvm_mmu_paging_element`: Page table entry access
- `mark_mmio_spte`: MMIO region access
- `fast_page_fault`: Fast page fault path

---

## Intel VMX Implementation (arch/x86/kvm/vmx/)

This directory contains Intel VT-x (VMX - Virtual Machine Extensions) specific implementation. VMX is Intel's hardware virtualization technology.

---

### vmx.c (257,631 bytes)

**Purpose**: Main Intel VMX implementation - the core of Intel virtualization

**Key Responsibilities**:
- **VMX Initialization**: Detect and enable Intel VT-x
- **VMCS Management**: Virtual Machine Control Structure setup and access
- **VM Entry/Exit**: Execute guest code on Intel CPUs
- **VMX Instructions**: VMLAUNCH, VMRESUME, VMREAD, VMWRITE
- **Exit Handling**: Handle all VMX exit reasons
- **Feature Enablement**: EPT, VPID, APICv, posted interrupts
- **Security**: VMX security features (SMEP, SMAP, etc.)

**VMCS (Virtual Machine Control Structure)**:
- Guest state area (CPU registers, CR3, GDTR, IDTR, etc.)
- Host state area (where to return on VM exit)
- VM execution controls (which events cause VM exit)
- VM exit controls (what to do on exit)
- VM entry controls (checks before entry)

**Key Functions**:
- `vmx_create_vcpu()`: Create VMX vCPU
- `vmx_vcpu_run()`: Execute guest code
- `vmx_handle_exit()`: Dispatch VMX exit handlers
- `vmx_set_cr0/cr3/cr4()`: Control register virtualization
- `ept_violation()`: EPT violation handler

**VMX Exit Reasons** (handled here):
- Exception/NMI
- External interrupt
- CPUID, HLT, INVLPG, RDTSC
- CR access (MOV to/from CR0, CR3, CR4)
- I/O instruction
- MSR access
- EPT violation/misconfiguration
- VMCALL (hypercall)

---

### vmx.h (23,175 bytes)

**Purpose**: VMX definitions and structures

**Contents**:
- VMX capability bits
- VMCS field encodings
- VMX data structures
- Function prototypes

---

### nested.c / nested.h (238,555 + 9,895 bytes)

**Purpose**: Nested VMX - run hypervisors inside VMs (L1, L2 virtualization)

**Key Responsibilities**:
- **L1 Hypervisor Support**: Allow guest to run its own VMs
- **VMCS Shadowing**: Manage L1 and L2 VMCS structures
- **Nested VM Entry/Exit**: Handle nested virtualization transitions
- **L1 ↔ L2 Switching**: Switch between nested guest levels

**Nested Virtualization Levels**:
```
L0: KVM (host hypervisor)
 └─ L1: Guest hypervisor (e.g., KVM, Hyper-V, VMware)
     └─ L2: Guest VM inside guest hypervisor
```

**Use Cases**:
- Run KVM inside KVM (development, testing)
- Run VMware Workstation in VM
- Cloud providers offering nested virtualization
- Kubernetes with nested VMs

**Performance**: L2 VMs run 10-20% slower than L1

**Complex Features**:
- VMCS12: L1 hypervisor's view of VMCS
- VMCS02: Actual hardware VMCS for L2
- Merging VMCS12 and VMCS01 into VMCS02

---

### vmcs.h (4,569 bytes)

**Purpose**: VMCS field definitions

**Contents**:
- VMCS field encodings (16-bit, 32-bit, 64-bit, natural-width)
- Field access macros
- VMCS component names

**Example Fields**:
- GUEST_RIP, GUEST_RSP, GUEST_RFLAGS
- GUEST_CR0, GUEST_CR3, GUEST_CR4
- GUEST_IDTR_BASE, GUEST_GDTR_BASE
- HOST_RIP, HOST_RSP, HOST_CR3

---

### vmcs12.c / vmcs12.h (7,132 + 14,099 bytes)

**Purpose**: VMCS12 structure for nested virtualization

**Key Responsibilities**:
- **L1 VMCS Format**: Define VMCS format for L1 hypervisor
- **Field Shadowing**: Shadow L1 VMCS fields
- **Synchronization**: Sync VMCS12 ↔ VMCS02

---

### vmcs_shadow_fields.h (3,115 bytes)

**Purpose**: VMCS shadowing field definitions

**VMCS Shadowing**: Hardware feature to avoid VM exits for VMREAD/VMWRITE in nested virt

---

### vmenter.S (9,268 bytes)

**Purpose**: VMX entry assembly code

**Key Responsibilities**:
- **VM Entry Path**: Low-level assembly for VMLAUNCH/VMRESUME
- **Register Save/Restore**: Save host state, restore guest state
- **Fast Path**: Optimized entry for performance

**Assembly Code**:
- Save host registers
- Load guest registers
- Execute VMLAUNCH or VMRESUME
- On VM exit: Save guest registers, restore host

---

### vmx_ops.h (10,374 bytes)

**Purpose**: VMX instruction wrappers

**Contents**:
- VMREAD, VMWRITE inline functions
- VMLAUNCH, VMRESUME wrappers
- VMCLEAR, VMPTRLD helpers

**Example**:
```c
static inline void vmcs_write32(unsigned long field, u32 value) {
    __vmwrite(field, value);
}
```

---

### capabilities.h (9,569 bytes)

**Purpose**: VMX capability detection

**Key Responsibilities**:
- **Feature Detection**: Detect VMX features via MSRs
- **Capability Bits**: EPT, VPID, APICv, unrestricted guest, etc.
- **Configuration**: Enable/disable features

**VMX Capabilities Detected**:
- EPT (Extended Page Tables)
- VPID (Virtual Processor ID)
- Unrestricted guest (run real mode without emulation)
- APICv (APIC virtualization)
- Posted interrupts
- PML (Page Modification Logging)
- VMCS shadowing

---

### common.h (5,186 bytes)

**Purpose**: Common VMX/SVM definitions

**Contents**: Shared structures between Intel VMX and AMD SVM

---

### posted_intr.c / posted_intr.h (10,236 + 902 bytes)

**Purpose**: Posted Interrupts support

**Key Responsibilities**:
- **APICv Feature**: Advanced interrupt delivery
- **Non-Exiting Interrupts**: Deliver interrupts without VM exit
- **Posted Interrupt Descriptor**: Data structure for pending interrupts
- **Performance**: Reduce interrupt latency

**How Posted Interrupts Work**:
1. External interrupt arrives
2. Hardware checks Posted Interrupt Descriptor
3. If guest running: Inject directly (no VM exit)
4. If guest not running: Schedule VM entry with interrupt

**Performance**: 50% reduction in interrupt overhead

---

### pmu_intel.c / pmu_intel.h (22,470 + 751 bytes)

**Purpose**: Intel Performance Monitoring Unit virtualization

**Key Responsibilities**:
- **Intel PMU**: Virtualize Intel-specific performance counters
- **Architectural PMU**: Version 1-5 support
- **Fixed Counters**: Instructions, cycles, reference cycles
- **Programmable Counters**: 4-8 general-purpose counters

**Intel PMU Versions**:
- v1: Basic (Core 2)
- v2: More counters (Nehalem)
- v3: AnyThread deprecated
- v4: Streamlined (Skylake)
- v5: Extended (Ice Lake)

---

### sgx.c / sgx.h (15,423 + 878 bytes)

**Purpose**: Intel SGX (Software Guard Extensions) virtualization

**Key Responsibilities**:
- **SGX Support**: Virtualize Intel SGX enclaves
- **EPC Management**: Enclave Page Cache virtualization
- **ENCLS Instructions**: Emulate SGX instructions
- **Attestation**: Support SGX remote attestation

**What is SGX?**
- Secure enclaves in user space
- Memory encrypted by CPU
- Protected from OS, hypervisor, physical attacks

**Use Case**: Run SGX applications in VMs (confidential computing)

---

### tdx.c / tdx.h / tdx_arch.h / tdx_errno.h (100,533 + 5,739 + 4,617 + 1,562 bytes)

**Purpose**: Intel TDX (Trust Domain Extensions) support

**Key Responsibilities**:
- **Confidential VMs**: Hardware-encrypted virtual machines
- **TDX Module**: Interact with CPU TDX module
- **Protected Memory**: Guest memory encrypted with ephemeral keys
- **Attestation**: Remote attestation for trust verification

**What is TDX?**
- Next-gen confidential computing (after SGX)
- Entire VM encrypted (not just enclaves)
- Protected from host, hypervisor, physical attacks
- Hardware-based memory encryption (MKTME)

**TDX Architecture**:
```
┌────────────────────────────────────┐
│        Guest TD (Trust Domain)     │
│  - Encrypted memory                │
│  - Protected from host             │
├────────────────────────────────────┤
│      TDX Module (CPU firmware)     │
├────────────────────────────────────┤
│      KVM (Limited control)         │
├────────────────────────────────────┤
│      Hardware (CPU TEE)            │
└────────────────────────────────────┘
```

**TDX Files**:
- `tdx.c`: Main TDX implementation
- `tdx.h`: TDX structures and prototypes
- `tdx_arch.h`: TDX architecture definitions
- `tdx_errno.h`: TDX error codes

**Use Case**: Cloud computing with hardware-level security guarantees

---

### hyperv.c / hyperv.h (6,233 + 2,153 bytes)

**Purpose**: VMX-specific Hyper-V enlightenments

**Key Responsibilities**:
- **Hyper-V on VMX**: Hyper-V paravirt optimizations for Intel
- **Enlightened VMCS**: Hyper-V's optimized VMCS format
- **Nested Hyper-V**: Run Hyper-V as L1 on KVM

---

### hyperv_evmcs.c / hyperv_evmcs.h (14,707 + 5,196 bytes)

**Purpose**: Enlightened VMCS implementation

**Key Responsibilities**:
- **eVMCS**: Hyper-V's optimized VMCS format
- **Reduced VM Exits**: Fewer exits for nested virtualization
- **Clean Fields**: Dirty bit tracking for VMCS fields

**eVMCS Benefits**:
- 30% performance improvement for nested Hyper-V
- Less memory for VMCS storage
- Faster VMCS switching

---

### main.c (23,264 bytes)

**Purpose**: VMX module initialization

**Key Responsibilities**:
- **Module Init**: Initialize VMX module
- **Hardware Check**: Verify VT-x support
- **Feature Setup**: Enable VMX features
- **CPU Hotplug**: Handle CPU online/offline

**Initialization Steps**:
1. Check CPUID for VMX support
2. Check IA32_FEATURE_CONTROL MSR (BIOS must enable VT-x)
3. Allocate VMXON region (per CPU)
4. Execute VMXON instruction
5. Set up EPT, VPID, APICv

---

### run_flags.h (488 bytes)

**Purpose**: VMX run flags

**Contents**: Flags for controlling VMX entry behavior

---

### x86_ops.h (7,597 bytes)

**Purpose**: x86 operations function pointers for VMX

**Contents**: VMX implementations of x86_ops callbacks

---

### vmx_onhyperv.c / vmx_onhyperv.h (1,281 + 3,574 bytes)

**Purpose**: VMX running on Hyper-V

**Key Responsibilities**:
- **Nested on Hyper-V**: KVM with VMX running as guest on Hyper-V
- **Enlightenments**: Use Hyper-V features to optimize nested KVM

---

## AMD SVM Implementation (arch/x86/kvm/svm/)

This directory contains AMD-V (SVM - Secure Virtual Machine) specific implementation. SVM is AMD's hardware virtualization technology, equivalent to Intel's VMX.

---

### svm.c / svm.h (155,725 + 27,868 bytes)

**Purpose**: Main AMD SVM implementation

**Key Responsibilities**:
- **SVM Initialization**: Detect and enable AMD-V
- **VMCB Management**: Virtual Machine Control Block (AMD's version of VMCS)
- **VM Entry/Exit**: Execute guest code on AMD CPUs
- **SVM Instructions**: VMRUN, VMLOAD, VMSAVE
- **NPT Support**: Nested Page Tables (AMD's version of EPT)
- **AVIC**: Advanced Virtual Interrupt Controller

**VMCB (Virtual Machine Control Block)**:
- Similar to VMCS but different layout
- Guest state area
- Control area (intercepts, ASID, NPT pointer)
- Save area (segment registers, etc.)

**Key Functions**:
- `svm_create_vcpu()`: Create SVM vCPU
- `svm_vcpu_run()`: Execute guest (VMRUN)
- `handle_exit()`: Dispatch SVM exit handlers

**SVM Exit Codes**:
- CR access, MSR access, CPUID
- Exception, interrupt
- NPT fault
- VMRUN (nested virtualization)

---

### nested.c (55,979 bytes)

**Purpose**: Nested SVM support

**Key Responsibilities**:
- **Nested AMD-V**: Run hypervisor inside AMD VM
- **VMCB12 Management**: L1 hypervisor's VMCB
- **Nested Intercepts**: Merge L1 and L0 intercepts

**Simpler than VMX Nested**: AMD hardware provides better nested virt support

---

### avic.c (36,524 bytes)

**Purpose**: AVIC (Advanced Virtual Interrupt Controller)

**Key Responsibilities**:
- **AMD APICv**: AMD's version of APIC virtualization
- **Non-Exiting Interrupts**: Deliver interrupts without VM exit
- **Doorbell**: Physical APIC backing for virtual APIC

**AVIC vs. APICv**: Different hardware implementation, same goal

---

### sev.c (142,681 bytes)

**Purpose**: AMD SEV (Secure Encrypted Virtualization)

**Key Responsibilities**:
- **Memory Encryption**: Encrypt VM memory with CPU key
- **SEV**: Basic memory encryption
- **SEV-ES**: Encrypted state (registers also encrypted)
- **SEV-SNP**: Secure Nested Paging (integrity protection)

**SEV Family**:
1. **SEV**: Memory encrypted, hypervisor can't read RAM
2. **SEV-ES**: Registers encrypted, hypervisor can't read CPU state
3. **SEV-SNP**: Memory integrity protection, prevent replay attacks

**SEV Architecture**:
```
Guest (C-bit set in page tables = encrypted)
  ↓
Memory Encryption Engine
  ↓
Encrypted DRAM (host can't read)
```

**Use Case**: Confidential computing on AMD processors

---

### pmu.c (6,257 bytes)

**Purpose**: AMD PMU virtualization

**Key Responsibilities**:
- **AMD PMU**: Virtualize AMD performance counters
- **IBS**: Instruction-Based Sampling support

---

### svm_ops.h (1,451 bytes)

**Purpose**: SVM instruction wrappers

**Contents**: Inline functions for VMRUN, VMLOAD, VMSAVE, etc.

---

### hyperv.c / hyperv.h (514 + 1,554 bytes)

**Purpose**: SVM-specific Hyper-V enlightenments

---

### svm_onhyperv.c / svm_onhyperv.h (1,644 + 2,224 bytes)

**Purpose**: SVM running on Hyper-V

---

### vmenter.S (10,018 bytes)

**Purpose**: SVM entry assembly code

**Key Responsibilities**:
- **VMRUN Path**: Low-level assembly for VMRUN
- **State Save/Restore**: Fast guest/host switching

---

## Header Files and APIs

### include/linux/kvm_host.h

**Purpose**: Main KVM host kernel API

**Contents**:
- Core KVM structures (`struct kvm`, `struct kvm_vcpu`)
- KVM function prototypes
- Architecture-independent interface

---

### include/uapi/linux/kvm.h

**Purpose**: Userspace KVM API (ioctl interface)

**Contents**:
- KVM ioctl numbers
- Userspace-visible structures
- ABI definitions for QEMU/libvirt

**Key ioctls**:
- `KVM_CREATE_VM`: Create VM
- `KVM_CREATE_VCPU`: Create vCPU
- `KVM_RUN`: Run vCPU
- `KVM_SET_USER_MEMORY_REGION`: Map memory
- `KVM_GET/SET_REGS`: Access registers
- `KVM_IRQ_LINE`: Inject interrupt

---

## Summary Statistics

### File Count by Directory

| Directory | Files | Total Lines (approx) |
|-----------|-------|---------------------|
| virt/kvm/ | 17 | 270,000 |
| arch/x86/kvm/ | 34 | 950,000 |
| arch/x86/kvm/mmu/ | 12 | 410,000 |
| arch/x86/kvm/vmx/ | 31 | 770,000 |
| arch/x86/kvm/svm/ | 12 | 600,000 |
| **Total** | **106** | **~3,000,000** |

### Largest Files

1. **x86.c** - 396,081 bytes (Main x86 implementation)
2. **vmx.c** - 257,631 bytes (Intel VMX core)
3. **nested.c (vmx)** - 238,555 bytes (Nested VMX)
4. **mmu.c** - 232,014 bytes (MMU implementation)
5. **kvm_main.c** - 170,748 bytes (Core KVM)
6. **svm.c** - 155,725 bytes (AMD SVM core)
7. **emulate.c** - 145,223 bytes (Instruction emulator)
8. **sev.c** - 142,681 bytes (AMD SEV)

### Key Technologies

| Technology | Files | Purpose |
|------------|-------|---------|
| Intel VMX | 31 | Intel VT-x virtualization |
| AMD SVM | 12 | AMD-V virtualization |
| EPT/NPT | 12 | Hardware-assisted paging |
| Nested Virt | 2 | Hypervisor-in-VM |
| TDX | 4 | Intel confidential computing |
| SEV | 1 | AMD confidential computing |
| Hyper-V | 8 | Microsoft paravirtualization |
| Xen | 2 | Xen paravirtualization |

---

## KVM Architecture Deep Dive

### Complete VM Execution Flow

```
1. Userspace (QEMU) opens /dev/kvm
2. ioctl(KVM_CREATE_VM) → kvm_create_vm()
3. ioctl(KVM_CREATE_VCPU) → kvm_vm_ioctl_create_vcpu()
4. ioctl(KVM_SET_USER_MEMORY_REGION) → kvm_set_memory_region()
5. ioctl(KVM_RUN) → kvm_vcpu_ioctl_run()
   ↓
6. kvm_arch_vcpu_ioctl_run() [x86.c]
   ↓
7. vcpu_enter_guest() [x86.c]
   ↓
8. kvm_x86_ops.run(vcpu) → vmx_vcpu_run() or svm_vcpu_run()
   ↓
9. VMLAUNCH/VMRESUME (Intel) or VMRUN (AMD)
   ↓
10. Guest executes...
   ↓
11. VM Exit (CPUID, I/O, EPT fault, etc.)
   ↓
12. vmx_handle_exit() or handle_exit()
   ↓
13. Exit handler (kvm_emulate_cpuid, handle_ept_violation, etc.)
   ↓
14. Return to step 9 (re-enter guest) or return to QEMU
```

### Memory Virtualization Stack

```
Guest Virtual Address (GVA)
   ↓ Guest page tables (CR3)
Guest Physical Address (GPA)
   ↓ EPT/NPT (hardware)
Host Physical Address (HPA)
```

### Interrupt Delivery Path

```
Physical Device
   ↓
VFIO (if passthrough) or QEMU emulation
   ↓
eventfd / irqfd
   ↓
KVM irqchip (IOAPIC/LAPIC emulation)
   ↓
Posted interrupts (if enabled) or VM entry with interrupt
   ↓
Guest IDT handler
```

---

## Development and Debugging

### Key Source Files to Read (in order)

1. **virt/kvm/kvm_main.c** - Understand core KVM
2. **arch/x86/kvm/x86.c** - Understand x86 virtualization
3. **arch/x86/kvm/vmx/vmx.c** - Understand Intel implementation
4. **arch/x86/kvm/mmu/mmu.c** - Understand memory virtualization
5. **include/uapi/linux/kvm.h** - Understand userspace API

### Building KVM Module

```bash
# Enable KVM in kernel config
make menuconfig
  Virtualization →
    [*] Kernel-based Virtual Machine (KVM) support
    [*]   KVM for Intel processors support
    [*]   KVM for AMD processors support

# Build kernel
make -j$(nproc)
make modules_install
make install

# Or build as module
make M=arch/x86/kvm modules
insmod arch/x86/kvm/kvm.ko
insmod arch/x86/kvm/kvm-intel.ko  # or kvm-amd.ko
```

### Debugging KVM

```bash
# Enable KVM tracing
cd /sys/kernel/debug/tracing
echo 1 > events/kvm/enable
cat trace_pipe

# Monitor VM exits
perf kvm stat record -p <qemu-pid>
perf kvm stat report

# Check KVM stats
cat /sys/kernel/debug/kvm/<vm-id>/vcpu0/stats
```

---

## Performance Tuning

### CPU Features for Performance

| Feature | Benefit | Impact |
|---------|---------|--------|
| EPT/NPT | Hardware paging | 40% faster than shadow |
| VPID | Tagged TLB | 30% fewer TLB flushes |
| APICv/AVIC | Interrupt virtualization | 50% lower interrupt latency |
| Posted Interrupts | Direct interrupt delivery | No VM exit for interrupts |
| Huge pages | Large page mappings | 20-30% memory performance |
| CPU pinning | NUMA locality | 15-25% better cache usage |

### KVM Module Parameters

```bash
# Intel
modprobe kvm-intel nested=1 ept=1 vpid=1 enable_apicv=1

# AMD
modprobe kvm-amd nested=1 npt=1 avic=1

# Common
modprobe kvm halt_poll_ns=200000
```

---

## Security Features

### Isolation Mechanisms

1. **Hardware Isolation**:
   - VMX/SVM: CPU ring -1
   - EPT/NPT: Memory isolation
   - IOMMU: Device DMA protection

2. **Confidential Computing**:
   - **Intel TDX**: Hardware VM encryption
   - **AMD SEV/SEV-ES/SEV-SNP**: Memory + register encryption

3. **Attack Surface Reduction**:
   - Minimal VM exit handlers
   - VMCS/VMCB validation
   - Guest state sanitization

---

## Use Cases and Applications

### Production Workloads

1. **Cloud Computing**:
   - AWS EC2 (uses KVM)
   - Google Compute Engine (uses KVM)
   - OpenStack (uses KVM/QEMU)

2. **Enterprise Virtualization**:
   - Red Hat Virtualization (KVM)
   - Proxmox VE (KVM/QEMU)
   - oVirt (KVM)

3. **Container Platforms**:
   - Kata Containers (KVM-based)
   - Firecracker (minimal KVM)
   - gVisor (KVM option)

4. **Development**:
   - Android Emulator (uses KVM)
   - QEMU development
   - Kernel testing

---

## Future Directions

### Upcoming Features

1. **TDX/SEV-SNP**: Widespread confidential computing
2. **FRED**: Flexible Return and Event Delivery (faster interrupts)
3. **LAM**: Linear Address Masking
4. **CET**: Control-flow Enforcement Technology (shadow stack)
5. **AMX**: Advanced Matrix Extensions virtualization

### Ongoing Optimization

- **Rust in KVM**: Memory safety for critical paths
- **io_uring**: Async I/O for QEMU/KVM interface
- **MGLRU**: Multi-generational LRU for guest memory
- **TDP MMU improvements**: Better scalability

---

## References and Resources

### Official Documentation

- **Linux KVM**: https://www.linux-kvm.org/
- **Kernel Documentation**: Documentation/virt/kvm/
- **QEMU**: https://www.qemu.org/
- **Intel SDM**: Software Developer's Manual (VMX spec)
- **AMD APM**: AMD64 Architecture Programmer's Manual (SVM spec)

### Source Code Locations

```
Linux kernel source tree:
virt/kvm/              → Core KVM (arch-independent)
arch/x86/kvm/          → x86 KVM implementation
  ├── vmx/             → Intel VMX (VT-x)
  ├── svm/             → AMD SVM (AMD-V)
  └── mmu/             → Memory management
include/linux/kvm*.h   → Kernel KVM headers
include/uapi/linux/kvm.h → Userspace API
```

### Community

- **Mailing List**: kvm@vger.kernel.org
- **IRC**: #kvm on irc.oftc.net
- **Patchwork**: https://patchwork.kernel.org/project/kvm/

---

## Conclusion

This document provides a comprehensive file-by-file reference for the KVM source code. The KVM subsystem is one of the most complex parts of the Linux kernel, with over 3 million lines of code spanning:

- **Core virtualization framework** (virt/kvm/)
- **x86 architecture support** (arch/x86/kvm/)
- **Intel VMX implementation** (arch/x86/kvm/vmx/)
- **AMD SVM implementation** (arch/x86/kvm/svm/)
- **Memory management** (arch/x86/kvm/mmu/)

Each file plays a crucial role in providing efficient, secure, and feature-rich virtualization on Linux systems.

---

**Document Author**: KVM Documentation Project
**License**: GPL-2.0-only (matching KVM source)
**Contributions**: Welcome via GitHub issues/PRs
