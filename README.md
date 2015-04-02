# phasm
Phasm is a generic assembler or binary generation language that is
thoroughly incomplete, but might be useful at some point.

A very basic example program and how to run it:

```python
#!/usr/bin/env phasm

std = Import("gh:aliclark/phasm-scratch/master/std.py")
asm = Import("gh:aliclark/phasm-scratch/master/asm_x64.py")

abstract_elf  = Import("gh:aliclark/phasm-scratch/master/elf.psm")
abstract_sys  = Import("gh:aliclark/phasm-scratch/master/linux-syscall-x64.psm")
abstract_do   = Import("gh:aliclark/phasm-scratch/master/do.psm")
abstract_util = Import("gh:aliclark/phasm-scratch/master/util.psm")

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

jge_1b = (to) -> {
    asm.jge_1b(from, to)
    :from:
}
jmp_1b = (to) -> {
    asm.jmp_1b(from, to)
    :from:
}

# n can be up to 256
loop = (n, code) -> {
    asm.mov_eax(U(4, 0))

    :loop:
    asm.cmp_eax_1b(n)
    jge_1b(end)

    asm.push_rax()

    code()

    asm.pop_rax()
    asm.add_eax_1b(1)
    jmp_1b(loop)

    :end:
}

text = (rodata, data) -> {

    # TODO: seccomp2 ourselves down to just sys_write and sys_exit

    loop(3, {
        sys.write(sys.fd_stdout, rodata.somestring2, 5)
    })

    loop(2, {
        sys.write(sys.fd_stdout, rodata.somestring, 7)
    })

    sys.exit(43)

    # signal to the user that this process should be terminated, if
    # not already done so
    :terminated:
    jmp_1b(terminated)
}

elf.linux(rodata, data, text)
```

To make it go:

```sh
# WARNING: I take no responsibility for any harm caused to your
# computer by running any of these commands!
######### Run at your own risk. #########

# check out the stuff
mkdir $HOME/projects
cd projects
git clone https://github.com/aliclark/phasm.git
cd -

# add phasm.sh to PATH as "phasm"
mkdir $HOME/bin
export PATH="$PATH:$HOME/bin"
ln -s /home/user/phasm/phasm.sh phasm

# download the code from the internet and run it
phasm gh:aliclark/phasm-scratch/master/program.psm
```

This is an exceedingly early release, so likely contains bugs, could
delete your hard-drive, etc. etc.

Hope you like it, any patches are very welcome!
