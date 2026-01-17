"use client"

import * as React from "react"
import { cn } from "@/lib/utils"
import { ChevronDown } from "lucide-react"

// Simple Select implementation without Radix dependency

interface SelectProps {
    value: string
    onValueChange: (value: string) => void
    children: React.ReactNode
    className?: string
}

interface SelectTriggerProps {
    children: React.ReactNode
    className?: string
}

interface SelectContentProps {
    children: React.ReactNode
}

interface SelectItemProps {
    value: string
    children: React.ReactNode
}

interface SelectValueProps {
    placeholder?: string
}

const SelectContext = React.createContext<{
    value: string
    onValueChange: (value: string) => void
    open: boolean
    setOpen: (open: boolean) => void
}>({
    value: "",
    onValueChange: () => { },
    open: false,
    setOpen: () => { }
})

const Select = ({ value, onValueChange, children, className }: SelectProps) => {
    const [open, setOpen] = React.useState(false)

    return (
        <SelectContext.Provider value={{ value, onValueChange, open, setOpen }}>
            <div className={cn("relative", className)}>
                {children}
            </div>
        </SelectContext.Provider>
    )
}

const SelectTrigger = React.forwardRef<HTMLButtonElement, SelectTriggerProps>(
    ({ children, className }, ref) => {
        const { open, setOpen } = React.useContext(SelectContext)

        return (
            <button
                ref={ref}
                type="button"
                onClick={() => setOpen(!open)}
                className={cn(
                    "flex h-10 w-full items-center justify-between rounded-md border border-white/10 bg-black/30 px-3 py-2 text-sm ring-offset-background placeholder:text-gray-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50",
                    className
                )}
            >
                {children}
                <ChevronDown className="h-4 w-4 opacity-50" />
            </button>
        )
    }
)
SelectTrigger.displayName = "SelectTrigger"

const SelectValue = ({ placeholder }: SelectValueProps) => {
    const { value } = React.useContext(SelectContext)
    return <span>{value || placeholder}</span>
}

const SelectContent = ({ children }: SelectContentProps) => {
    const { open, setOpen } = React.useContext(SelectContext)

    if (!open) return null

    return (
        <>
            <div
                className="fixed inset-0 z-40"
                onClick={() => setOpen(false)}
            />
            <div className="absolute top-full left-0 z-50 mt-1 w-full rounded-md border border-white/10 bg-[#1a1a2e] py-1 text-white shadow-lg">
                {children}
            </div>
        </>
    )
}

const SelectItem = ({ value, children }: SelectItemProps) => {
    const { onValueChange, setOpen, value: currentValue } = React.useContext(SelectContext)

    return (
        <div
            onClick={() => {
                onValueChange(value)
                setOpen(false)
            }}
            className={cn(
                "cursor-pointer px-3 py-2 text-sm hover:bg-white/10",
                currentValue === value && "bg-violet-500/20 text-violet-300"
            )}
        >
            {children}
        </div>
    )
}

export { Select, SelectTrigger, SelectContent, SelectItem, SelectValue }
