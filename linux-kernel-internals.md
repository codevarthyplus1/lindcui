# Linux Kernel Internals: Core Areas Review

## Table of Contents
1. [Introduction](#introduction)
2. [Kernel Architecture](#kernel-architecture)
3. [Process Management](#process-management)
4. [Memory Management](#memory-management)
5. [File Systems and VFS](#file-systems-and-vfs)
6. [Device Drivers](#device-drivers)
7. [Networking Stack](#networking-stack)
8. [System Calls](#system-calls)
9. [Interrupt Handling](#interrupt-handling)
10. [Process Scheduling](#process-scheduling)
11. [Synchronization Mechanisms](#synchronization-mechanisms)
12. [Kernel Modules](#kernel-modules)

---

## Introduction

The Linux kernel is a monolithic, modular, multitasking, Unix-like operating system kernel. It serves as the core interface between a computer's hardware and its processes, managing system resources and providing essential services to user-space applications.

**Key Characteristics:**
- **Monolithic**: Core functionality runs in kernel space with high privileges
- **Modular**: Supports dynamically loadable kernel modules
- **Portable**: Runs on various hardware architectures (x86, ARM, RISC-V, etc.)
- **Open Source**: Licensed under GPLv2

---

## Kernel Architecture

### Kernel Space vs User Space

The Linux kernel operates in a privileged mode (kernel space) with direct hardware access, while user applications run in user space with restricted privileges.

**Memory Layout:**
```
┌─────────────────────┐ 0xFFFFFFFF (4GB on 32-bit)
│   Kernel Space      │
│   - Kernel code     │
│   - Kernel data     │
│   - Device drivers  │
├─────────────────────┤ 0xC0000000 (typical)
│   User Space        │
│   - Applications    │
│   - Libraries       │
│   - Stack/Heap      │
└─────────────────────┘ 0x00000000
```

### Major Subsystems

1. **Process Scheduler**: Manages CPU time allocation
2. **Memory Manager**: Handles virtual memory and paging
3. **Virtual File System (VFS)**: Abstracts file system operations
4. **Network Stack**: Implements network protocols
5. **Device Drivers**: Hardware abstraction layer
6. **Inter-Process Communication (IPC)**: Facilitates process communication

---

## Process Management

### Task Structure

Each process is represented by a `task_struct` (defined in `include/linux/sched.h`), which contains:
- Process state (running, sleeping, stopped, zombie)
- Process ID (PID) and parent PID
- Memory management information
- File descriptors
- CPU registers and context
- Scheduling information
- Signal handlers

### Process States

```
TASK_RUNNING          → Process is runnable
TASK_INTERRUPTIBLE    → Process is sleeping, can be woken by signals
TASK_UNINTERRUPTIBLE  → Process is sleeping, cannot be interrupted
TASK_STOPPED          → Process execution stopped (SIGSTOP)
TASK_TRACED           → Process being traced by debugger
EXIT_ZOMBIE           → Process terminated, waiting for parent
EXIT_DEAD             → Process being removed
```

### Process Creation

**System Calls:**
- `fork()`: Creates child process (copy-on-write)
- `vfork()`: Creates child process without copying page tables
- `clone()`: Creates threads with shared resources
- `execve()`: Replaces current process image

**Process Flow:**
1. `fork()` duplicates the parent's task_struct
2. Copy-on-write (COW) mechanism shares memory pages
3. Child gets unique PID
4. Both processes continue execution from fork() return

### Process Termination

1. Process calls `exit()` system call
2. Kernel releases process resources
3. Process enters zombie state
4. Parent calls `wait()` to collect exit status
5. Kernel removes process completely

---

## Memory Management

### Virtual Memory

Linux uses virtual memory to provide:
- **Isolation**: Each process has its own address space
- **Protection**: Prevent unauthorized memory access
- **Swapping**: Use disk as extended RAM

### Page Tables

**Multi-level Paging (x86-64):**
```
Virtual Address → PGD → PUD → PMD → PTE → Physical Page
```

- **PGD**: Page Global Directory
- **PUD**: Page Upper Directory
- **PMD**: Page Middle Directory
- **PTE**: Page Table Entry

### Memory Zones

```
ZONE_DMA       → 0-16MB (ISA DMA)
ZONE_DMA32     → 0-4GB (32-bit DMA devices)
ZONE_NORMAL    → Normal memory
ZONE_HIGHMEM   → High memory (>896MB on 32-bit)
ZONE_MOVABLE   → Movable pages for memory hotplug
```

### Memory Allocation

**Kernel Allocators:**

1. **Buddy System**:
   - Allocates pages in power-of-2 sizes
   - Reduces external fragmentation
   - Used by `__get_free_pages()`

2. **Slab Allocator** (SLUB):
   - Caches frequently used objects
   - Reduces allocation overhead
   - Used by `kmalloc()` and `kmem_cache_alloc()`

3. **vmalloc**:
   - Allocates virtually contiguous memory
   - May not be physically contiguous
   - Used for large kernel buffers

### Page Replacement

**Algorithms:**
- **LRU (Least Recently Used)**: Evicts least recently used pages
- **Two-list strategy**: Active and inactive page lists
- **Page cache**: Caches file data in memory

### Out of Memory (OOM) Killer

When system runs out of memory:
1. OOM killer selects process to terminate
2. Scoring based on memory usage and importance
3. Sends SIGKILL to selected process
4. Reclaims memory

---

## File Systems and VFS

### Virtual File System (VFS)

VFS provides a common interface for different file systems:

**Key Data Structures:**
```c
struct super_block    // File system metadata
struct inode          // File metadata (permissions, size, etc.)
struct dentry         // Directory entry (path component)
struct file           // Open file instance
```

**VFS Objects Relationships:**
```
superblock → inode → dentry → file
```

### File Operations

**Common Operations:**
```c
struct file_operations {
    ssize_t (*read)(struct file *, char __user *, size_t, loff_t *);
    ssize_t (*write)(struct file *, const char __user *, size_t, loff_t *);
    int (*open)(struct inode *, struct file *);
    int (*release)(struct inode *, struct file *);
    int (*mmap)(struct file *, struct vm_area_struct *);
    // ... more operations
};
```

### Common File Systems

1. **ext4**: Default Linux file system
   - Journaling for crash recovery
   - Supports large files (16TB) and volumes (1EB)
   - Delayed allocation

2. **XFS**: High-performance file system
   - Excellent for large files
   - Online defragmentation
   - Metadata journaling

3. **Btrfs**: Modern copy-on-write file system
   - Snapshots and cloning
   - Built-in RAID support
   - Checksums for data integrity

4. **tmpfs/shmfs**: RAM-based file systems
5. **procfs**: Process information pseudo-file system
6. **sysfs**: Device and driver information

### Page Cache

- Caches file data in RAM
- Reduces disk I/O operations
- Write-back and write-through modes
- Managed by the page replacement algorithm

---

## Device Drivers

### Character Devices

- Stream-based I/O (byte-by-byte)
- Examples: terminals, serial ports, keyboards
- Accessed through `/dev/` entries
- Operations: read, write, ioctl

### Block Devices

- Block-based I/O (fixed-size blocks)
- Examples: hard drives, SSDs, USB storage
- Uses buffer cache for performance
- Supports scheduling algorithms (CFQ, Deadline, NOOP)

### Network Devices

- Handle network packets
- Examples: Ethernet cards, WiFi adapters
- Special interface (not file-based)
- Accessed through sockets

### Driver Architecture

**Key Structures:**
```c
struct cdev           // Character device
struct block_device   // Block device
struct net_device     // Network device
struct device_driver  // Generic driver
```

**Driver Registration:**
1. Module initialization (`module_init`)
2. Device registration (`register_chrdev`, `register_blkdev`)
3. Device operations setup
4. Resource allocation

**Device Model:**
```
Bus → Device → Driver
```

### Hardware Interaction

**Methods:**
1. **Port I/O**: `inb()`, `outb()` for x86
2. **Memory-mapped I/O (MMIO)**: `ioread32()`, `iowrite32()`
3. **DMA (Direct Memory Access)**: Hardware accesses memory directly
4. **Interrupts**: Hardware signals events to CPU

---

## Networking Stack

### OSI Model in Linux

```
Application Layer    → User-space applications (sockets)
Transport Layer      → TCP, UDP, SCTP
Network Layer        → IP, ICMP, routing
Data Link Layer      → Ethernet, WiFi, ARP
Physical Layer       → Network device drivers
```

### Socket Buffer (sk_buff)

Core data structure for network packets:
```c
struct sk_buff {
    struct net_device *dev;        // Network device
    unsigned char *head;           // Buffer start
    unsigned char *data;           // Current data pointer
    unsigned char *tail;           // End of data
    unsigned char *end;            // Buffer end
    // ... more fields
};
```

### Packet Processing Flow

**Receive Path:**
1. NIC receives packet → DMA to memory
2. Hardware interrupt triggers
3. Driver allocates sk_buff
4. Packet moves up protocol stack
5. Data delivered to socket buffer
6. Application reads via `recv()`

**Transmit Path:**
1. Application writes via `send()`
2. Data copied to sk_buff
3. Packet moves down protocol stack
4. Queued in device queue (qdisc)
5. Driver transmits via NIC
6. sk_buff freed after transmission

### Netfilter/iptables

**Hooks in packet path:**
```
PREROUTING → FORWARD → POSTROUTING
           ↘ INPUT → OUTPUT ↗
```

Used for:
- Packet filtering (firewall)
- NAT (Network Address Translation)
- Packet mangling
- Connection tracking

### Network Namespaces

Isolate network stack per namespace:
- Separate routing tables
- Firewall rules
- Network devices
- Used by containers (Docker, Kubernetes)

---

## System Calls

### System Call Interface

System calls provide controlled entry from user space to kernel space.

**Common System Calls:**
```c
// Process management
fork(), execve(), exit(), wait()

// File operations
open(), read(), write(), close(), ioctl()

// Memory management
brk(), mmap(), munmap()

// Signals
kill(), signal(), sigaction()

// Network
socket(), bind(), listen(), accept(), connect()
```

### System Call Mechanism

**x86-64 Process:**
1. User program sets syscall number in RAX
2. Arguments in RDI, RSI, RDX, R10, R8, R9
3. Execute `syscall` instruction
4. CPU switches to kernel mode
5. Kernel dispatches to syscall handler
6. Handler executes requested operation
7. Return to user mode with result in RAX

**System Call Table:**
```c
// arch/x86/entry/syscalls/syscall_64.tbl
0    common  read            sys_read
1    common  write           sys_write
2    common  open            sys_open
...
```

### Adding a System Call

1. Add entry to syscall table
2. Implement handler function
3. Define syscall number in header
4. Update unistd.h
5. Rebuild kernel

---

## Interrupt Handling

### Interrupt Types

1. **Hardware Interrupts (IRQ)**:
   - Triggered by devices (keyboard, disk, network)
   - Asynchronous to processor

2. **Software Interrupts**:
   - System calls (INT 0x80 on x86)
   - Exceptions (page faults, divide by zero)

3. **Exceptions**:
   - Synchronous events during execution
   - Page faults, invalid opcodes

### Interrupt Handling Flow

```
Hardware Event → IDT Lookup → IRQ Handler → Top Half
                                          ↓
                                     Bottom Half (Softirq/Tasklet/Workqueue)
```

**Top Half (Hard IRQ):**
- Runs in interrupt context
- Must be fast and non-blocking
- Acknowledges interrupt
- Schedules bottom half if needed

**Bottom Half:**
- Deferred processing
- Can be interrupted
- Three mechanisms:
  - **Softirqs**: High-priority, statically allocated
  - **Tasklets**: Built on softirqs, dynamically allocated
  - **Work queues**: Run in process context, can sleep

### Interrupt Descriptor Table (IDT)

Maps interrupt vectors to handlers:
```
Vector 0-31    → CPU exceptions
Vector 32-255  → Device interrupts and software interrupts
```

### Interrupt Context

Code running in interrupt context:
- Cannot sleep or block
- Cannot access user-space memory
- Limited stack space
- Should complete quickly

---

## Process Scheduling

### Completely Fair Scheduler (CFS)

Default scheduler since Linux 2.6.23:

**Key Concepts:**
- Virtual runtime (vruntime): CPU time consumed
- Red-black tree: Organizes runnable tasks
- Always picks task with smallest vruntime
- Fair distribution of CPU time

**Time Slicing:**
```
time_slice = (sched_latency * task_weight) / total_weight
```

### Scheduling Classes

Priority order (highest to lowest):
1. **Stop**: Highest priority (CPU hotplug)
2. **Deadline**: Real-time deadline scheduler
3. **Real-time**: SCHED_FIFO and SCHED_RR
4. **CFS**: Normal time-sharing tasks (SCHED_NORMAL)
5. **Idle**: Runs when nothing else is runnable

### Real-Time Scheduling

**SCHED_FIFO**:
- First-in, first-out
- Runs until blocks or yields
- No time slicing

**SCHED_RR**:
- Round-robin with time slicing
- Tasks with same priority rotate

**SCHED_DEADLINE**:
- Earliest Deadline First (EDF)
- Guarantees task completes by deadline
- Most advanced real-time scheduler

### Priority and Nice Values

```
Nice values:    -20 to +19 (lower = higher priority)
Real-time:      0 to 99 (higher = higher priority)
Normal tasks:   100 to 139 (mapped from nice values)
```

### Load Balancing

Distributes tasks across CPUs:
- Per-CPU run queues
- Periodic balancing
- Migration cost consideration
- NUMA awareness

### Context Switching

Process of saving/restoring process state:
1. Save current task registers
2. Update task_struct state
3. Switch page tables (CR3 on x86)
4. Restore new task registers
5. Resume execution

**Overhead**: 1-10 microseconds depending on architecture

---

## Synchronization Mechanisms

### Why Synchronization?

- Race conditions in concurrent access
- Critical sections need protection
- Data consistency requirements

### Atomic Operations

Indivisible operations on memory:
```c
atomic_t counter;
atomic_inc(&counter);
atomic_dec(&counter);
atomic_read(&counter);
```

### Spinlocks

Busy-wait locks for short critical sections:
```c
spinlock_t lock;
spin_lock_init(&lock);
spin_lock(&lock);
// Critical section
spin_unlock(&lock);
```

**Characteristics:**
- Wastes CPU cycles while waiting
- Use when lock held briefly
- Cannot sleep while holding

**Variants:**
- `spin_lock_irqsave()`: Disables local interrupts
- `spin_lock_bh()`: Disables bottom halves

### Semaphores

Sleeping locks, can be held longer:
```c
struct semaphore sem;
sema_init(&sem, 1);  // Binary semaphore
down(&sem);          // Acquire
// Critical section
up(&sem);            // Release
```

**Use Cases:**
- Can sleep while waiting
- Longer critical sections
- Not usable in interrupt context

### Mutexes

Optimized mutual exclusion locks:
```c
struct mutex lock;
mutex_init(&lock);
mutex_lock(&lock);
// Critical section
mutex_unlock(&lock);
```

**Advantages over semaphores:**
- Simpler semantics (always binary)
- Better debugging support
- Optimized for common case
- Must be released by same thread

### Read-Write Locks

Allow multiple readers or single writer:
```c
rwlock_t lock;
read_lock(&lock);    // Multiple readers allowed
read_unlock(&lock);

write_lock(&lock);   // Exclusive access
write_unlock(&lock);
```

### RCU (Read-Copy-Update)

Advanced synchronization for read-heavy workloads:
```c
rcu_read_lock();
ptr = rcu_dereference(global_ptr);
// Use ptr
rcu_read_unlock();
```

**Benefits:**
- Lock-free reads
- No cache bouncing
- Scalable on multicore
- Used extensively in networking

### Barriers

Memory and compiler barriers:
```c
barrier();          // Compiler barrier
mb();              // Memory barrier (read/write)
rmb();             // Read memory barrier
wmb();             // Write memory barrier
smp_mb();          // SMP memory barrier
```

---

## Kernel Modules

### What are Kernel Modules?

- Loadable code that extends kernel functionality
- Can be loaded/unloaded at runtime
- No need to reboot for changes
- Examples: device drivers, file systems, network protocols

### Module Structure

**Basic Module:**
```c
#include <linux/module.h>
#include <linux/kernel.h>
#include <linux/init.h>

static int __init my_module_init(void) {
    printk(KERN_INFO "Module loaded\n");
    return 0;
}

static void __exit my_module_exit(void) {
    printk(KERN_INFO "Module unloaded\n");
}

module_init(my_module_init);
module_exit(my_module_exit);

MODULE_LICENSE("GPL");
MODULE_AUTHOR("Your Name");
MODULE_DESCRIPTION("Module description");
```

### Module Operations

**Loading:**
```bash
insmod module.ko           # Insert module
modprobe module_name       # Load with dependencies
```

**Unloading:**
```bash
rmmod module_name          # Remove module
modprobe -r module_name    # Remove with dependencies
```

**Information:**
```bash
lsmod                      # List loaded modules
modinfo module.ko          # Module information
```

### Module Parameters

Allow runtime configuration:
```c
static int param = 0;
module_param(param, int, 0644);
MODULE_PARM_DESC(param, "Module parameter description");
```

Load with parameter:
```bash
insmod module.ko param=10
```

### Module Dependencies

Modules can depend on other modules:
```c
// Export symbols for other modules
EXPORT_SYMBOL(my_function);
EXPORT_SYMBOL_GPL(gpl_function);

// Use symbols from other modules
extern int other_function(void);
```

### Module Versioning

- **modversions**: Ensures ABI compatibility
- Kernel version checking
- Symbol version checking

---

## Advanced Topics

### Kernel Preemption

**Non-preemptive Kernel:**
- Kernel code runs to completion
- Poor latency

**Preemptive Kernel:**
- Higher priority task can interrupt
- Better responsiveness
- CONFIG_PREEMPT option

### NUMA (Non-Uniform Memory Access)

- Memory access time depends on location
- Per-node memory allocation
- NUMA-aware scheduling
- Important for large multiprocessor systems

### Namespaces and Cgroups

**Namespaces** (isolation):
- PID namespace: Process ID isolation
- Network namespace: Network stack isolation
- Mount namespace: File system isolation
- User namespace: UID/GID isolation
- IPC namespace: Inter-process communication isolation
- UTS namespace: Hostname isolation

**Cgroups** (resource limits):
- CPU quota
- Memory limits
- I/O bandwidth
- Network priority
- Used by containers

### Kernel Debugging

**Tools:**
- **printk()**: Kernel logging
- **kgdb**: Kernel debugger
- **ftrace**: Function tracing
- **perf**: Performance analysis
- **kdump/kexec**: Crash dumps
- **SystemTap**: Dynamic tracing

**Debug Options:**
- CONFIG_DEBUG_KERNEL
- CONFIG_DEBUG_INFO
- CONFIG_KASAN (address sanitizer)
- CONFIG_LOCKDEP (deadlock detection)

---

## Kernel Development

### Building the Kernel

```bash
# Configure
make menuconfig
make defconfig
make localmodconfig

# Build
make -j$(nproc)
make modules
make modules_install
make install
```

### Kernel Coding Style

- Tabs for indentation (8 characters)
- 80-character line limit
- K&R brace style
- Descriptive function names
- Use checkpatch.pl for validation

### Contributing to Linux

1. Join mailing lists (LKML)
2. Read Documentation/
3. Follow coding standards
4. Create patches with git format-patch
5. Submit via email to maintainers
6. Respond to feedback

---

## Performance Considerations

### System Call Overhead

- Context switch penalty
- Use batching when possible
- Consider vDSO for lightweight calls

### Cache Effects

- Keep hot data together
- Align structures to cache lines
- Minimize cache line bouncing
- Use per-CPU data

### Lock Contention

- Reduce critical section size
- Use RCU for read-heavy workloads
- Per-CPU variables avoid locking
- Lock-free algorithms where possible

### I/O Performance

- Use asynchronous I/O (io_uring)
- Batch operations
- Direct I/O for large transfers
- Page cache tuning

---

## Security Features

### Kernel Security Mechanisms

1. **Capabilities**: Fine-grained privileges
2. **SELinux/AppArmor**: Mandatory Access Control
3. **Seccomp**: System call filtering
4. **Namespaces**: Isolation
5. **ASLR**: Address Space Layout Randomization
6. **SMEP/SMAP**: Supervisor Mode Execution/Access Prevention

### Kernel Hardening

- Stack protection (canaries)
- Heap hardening
- Read-only memory regions
- Kernel page table isolation (KPTI)
- Control Flow Integrity (CFI)

---

## Conclusion

The Linux kernel is a sophisticated piece of software that manages hardware resources and provides essential services to applications. Understanding its internals requires knowledge of:

- **Process management**: How tasks are created, scheduled, and terminated
- **Memory management**: Virtual memory, paging, and allocation strategies
- **File systems**: VFS abstraction and specific implementations
- **Device drivers**: Hardware interaction and device models
- **Networking**: Protocol stack and packet processing
- **Synchronization**: Protecting critical sections in concurrent environments
- **System calls**: Interface between user and kernel space

This knowledge is essential for:
- Kernel developers
- System programmers
- Performance engineers
- Security researchers
- Embedded systems developers

### Resources for Further Learning

**Books:**
- "Linux Kernel Development" by Robert Love
- "Understanding the Linux Kernel" by Bovet & Cesati
- "Linux Device Drivers" by Corbet, Rubini, and Kroah-Hartman

**Online:**
- https://kernel.org - Official kernel source
- https://www.kernel.org/doc/ - Kernel documentation
- https://kernelnewbies.org/ - Beginner-friendly resources
- https://lwn.net/ - Linux Weekly News

**Source Code:**
- Read the source: `/usr/src/linux/`
- Start with `init/main.c` (kernel initialization)
- Follow code paths with cscope or ctags

---

*Document Version: 1.0*
*Last Updated: 2025-11-15*
