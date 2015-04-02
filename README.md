# phasm
Phasm is a generic assembler or binary generation language that is
thoroughly incomplete, but might be useful at some point.

A very basic example program and how to run it:

```python
(std, asm, elf, sys, util) -> {

    rodata = {
        lalala      = util.utf8("lalala\n")
        hello_world = util.utf8("Hello, world!\n")
        hiya        = util.utf8("hiya\n")

        :lalala_addr:      lalala
        :hello_world_addr: hello_world
        :hiya_addr:        hiya
    }

    data = {
        :counter: std.U(8, 0)
        :space:   std.Bin(8, "00 00 00 00 00 00 00 00")
    }

    text = (rodata, data) -> {

        # TODO: seccomp2 ourselves down to just sys_write and sys_exit

        util.loop(3, {
            sys.write(sys.fd_stdout, rodata.hiya_addr, rodata.hiya.len)
        })

        util.loop(2, {
            sys.write(sys.fd_stdout, rodata.lalala_addr, rodata.lalala.len)
        })

        sys.exit(43)

        # signal to the user that this process should be terminated, if
        # not already done so
        :terminated:
        asm.jmp_1b(terminated)
    }

    elf.linux(rodata, data, text)
}
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
ln -s $HOME/projects/phasm/phasm.sh $HOME/bin/phasm

# download the code from the internet and run it
phasm gh:aliclark/phasm-scratch/master/hello.psm
```

This is an exceedingly early release, so likely contains bugs, could
delete your hard-drive, etc. etc.

Hope you like it, any patches are very welcome!
