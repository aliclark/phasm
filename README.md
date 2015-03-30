# phasm
Phasm is a generic assembler or binary generation language that is
thoroughly incomplete, but might be useful at some point.

For an exmple of what the code looks like, please see
https://github.com/aliclark/phasm-scratch/blob/master/program.psm
and
https://github.com/aliclark/phasm-scratch/blob/master/elf.psm

Or just read a copy of program.psm that I pasted earlier:

```
#!/usr/bin/env phasm

std = Import("std")
asm = Import("asm_x64")

abstract_elf  = Import("elf")
abstract_sys  = Import("linux-syscall-x64")
abstract_do   = Import("do")
abstract_util = Import("util")

elf  = abstract_elf(std)
sys  = abstract_sys(std, asm)
do   = abstract_do(asm)
util = abstract_util(std, sys)

U = std.U
Bin = std.Bin

rodata = {
    :somestring:  util.utf8("lalala\n\0")
    :hello_world: util.utf8("Hello, world!\n\0")
    :somestring2: util.utf8("hiya\n\0")
}

data = {
    :counter: U(8, 0)
    :space:   Bin(8, "00 00 00 00 00 00 00 00")
}

# n can be up to 256
loop = (n, code) -> {
    asm.mov_eax(U(4, 0))

    :loop:
    asm.cmp_eax_1b(n)
    asm.jge_1b(cont, end)

    :cont:
    asm.push_rax()

    code()

    asm.pop_rax()
    asm.add_eax_1b(1)
    asm.jmp_1b(end, loop)

    :end:
}

text = (rodata, data) -> {

    loop(3, {
        sys.write(sys.fd_stdout, rodata.somestring2, 5)
    })

    loop(2, {
        sys.write(sys.fd_stdout, rodata.somestring, 7)
    })

    sys.exit(43)
}

elf.linux(rodata, data, text)
```

This is an exceedingly early release, so likely contains bugs, could
delete your harddrive, etc. etc.

Hope you like it, any patches are very welcome!
