# phasm
Phasm is a generic assembler or binary generation language that is
thoroughly incomplete, but might be useful at some point.

A very basic example program and how to run it:

```python
(std, asm, elf, sys, util) -> {

    rodata = {
        hello_world = util.utf8("Hello, world!\n")
        bye         = util.utf8("bye!\n")

        :hello_world_addr: hello_world
        :bye_addr:         bye
    }

    data = {
        :counter: std.U(8, 0)
    }

    text = (rodata, data) -> {

        # TODO: seccomp2 ourselves down to just sys_write and sys_exit

        util.print(rodata.hello_world_addr, rodata.hello_world.len)

        util.loop(2, {
            util.print(rodata.bye_addr, rodata.bye.len)
        })

        sys.exit(42)

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

Currently, this compiles and runs a binary of just 222 bytes:

00000000  7f 45 4c 46 02 01 01 03  00 00 00 00 00 00 00 00  |.ELF............|
00000010  02 00 3e 00 01 00 00 00  78 80 04 08 00 00 00 00  |..>.....x.......|
00000020  40 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |@...............|
00000030  00 00 00 00 40 00 38 00  01 00 00 00 00 00 00 00  |....@.8.........|
00000040  01 00 00 00 05 00 00 00  00 00 00 00 00 00 00 00  |................|
00000050  00 80 04 08 00 00 00 00  00 80 04 08 00 00 00 00  |................|
00000060  de 00 00 00 00 00 00 00  de 00 00 00 00 00 00 00  |................|
00000070  00 10 00 00 00 00 00 00  bb 01 00 00 00 b9 c3 80  |................|
00000080  04 08 ba 0e 00 00 00 b8  04 00 00 00 cd 80 b8 00  |................|
00000090  00 00 00 83 f8 02 7d 1d  50 bb 01 00 00 00 b9 d1  |......}.P.......|
000000a0  80 04 08 ba 05 00 00 00  b8 04 00 00 00 cd 80 58  |...............X|
000000b0  83 c0 01 eb de bb 2a 00  00 00 b8 01 00 00 00 cd  |......*.........|
000000c0  80 eb fe 48 65 6c 6c 6f  2c 20 77 6f 72 6c 64 21  |...Hello, world!|
000000d0  0a 62 79 65 21 0a 00 00  00 00 00 00 00 00        |.bye!.........|

This is an exceedingly early release, so likely contains bugs, could
delete your hard-drive, etc. etc.

Hope you like it, any patches are very welcome!
