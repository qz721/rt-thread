#ifndef __PLATFORM_H__
#define __PLATFORM_H__

#include <rthw.h>
#include <rtthread.h>

/* SOC-relative definitions */
//#include "realview.h"
#include "gic_registers.h"
#include "irq_numbers.h"

/* the maximum number of gic */
# define ARM_GIC_MAX_NR 1

/* the maximum number of interrupts */
#define ARM_GIC_NR_IRQS IMX_INTERRUPT_COUNT

/* the maximum entries of the interrupt table */
#define MAX_HANDLERS IMX_INTERRUPT_COUNT

/* the basic constants needed by gic */
#define GIC_DIST_BASE kGICDBaseOffset
#define GIC_CPU_BASE kGICCBaseOffset
#define GIC_IRQ_START   0

#define GIC_ACK_INTID_MASK              0x000003ff

/* the definition needed by gic.c */
#define __REG32(x)  (*((volatile unsigned int *)(x)))

/* keep compatible with platform SDK */
typedef enum {
    CPU_0,
    CPU_1,
    CPU_2,
    CPU_3,
} cpuid_e;

enum _gicd_sgi_filter
{
    //! Forward the interrupt to the CPU interfaces specified in the @a target_list parameter.
    kGicSgiFilter_UseTargetList = 0,

    //! Forward the interrupt to all CPU interfaces except that of the processor that requested
    //! the interrupt.
    kGicSgiFilter_AllOtherCPUs = 1,

    //! Forward the interrupt only to the CPU interface of the processor that requested the
    //! interrupt.
    kGicSgiFilter_OnlyThisCPU = 2
};

typedef void (*irq_hdlr_t) (void);

extern void rt_hw_interrupt_mask(int vector);
extern void rt_hw_interrupt_umask(int vector);
extern rt_isr_handler_t rt_hw_interrupt_install(int vector, rt_isr_handler_t handler,
    void *param, const char *name);

static inline void register_interrupt_routine(uint32_t irq_id, irq_hdlr_t isr)
{
    rt_hw_interrupt_install(irq_id, (rt_isr_handler_t)isr, NULL, "unknown");
}

static inline void enable_interrupt(uint32_t irq_id, uint32_t cpu_id, uint32_t priority)
{
    rt_hw_interrupt_umask(irq_id);
}

static inline void disable_interrupt(uint32_t irq_id, uint32_t cpu_id)
{
    rt_hw_interrupt_mask(irq_id);
}

#endif	// __PLATFORM_H__
