# phasm
Phasm is a generic assembler or binary generation language that is
thoroughly incomplete, but might be useful at some point.

A very basic example program and how to run it:

```ruby
(std, asm, elf, proc, sys, util) -> {

    data = {}
    bss  = {}

    rodata = {
        hello_world = util.utf8("Hello, world!\n")
        bye         = util.utf8("bye!\n")

        :hello_world_addr: hello_world
        :bye_addr:         bye
    }

    text = (rodata, data, bss) -> {
        :start: {
            proc.call2(print, rodata.hello_world_addr, rodata.hello_world.size)
            sys.exit(0)
        }

        :print: proc.sub2({
            asm.mov("rdx", "[rbp+24]")
            asm.mov("rcx", "[rbp+16]")
            asm.mov("rbx", sys.fd_stdout)
            sys.call(sys.sys_write)
        })
    }

    elf.linux_x64(rodata, data, bss, text)
}
```

To make it go:

```sh
# WARNING: I take no responsibility for any harm caused to your
# computer by running any of these commands!
######### Run at your own risk. #########

# check out the stuff
mkdir -p $HOME/projects
cd $HOME/projects
git clone https://github.com/aliclark/phasm.git
cd -

# add phasm.sh to PATH as "phasm"
mkdir -p $HOME/bin
export PATH="$PATH:$HOME/bin"
ln -sf $HOME/projects/phasm/phasm.sh $HOME/bin/phasm

# download the code from the internet and run it
phasm <(echo 'Import("gh:aliclark/phasm-scratch/0.2/hello-linux-x64.psm")')
```

This compiles and runs a binary of 207 bytes:

```
00000000  7f 45 4c 46 02 01 01 03  00 00 00 00 00 00 00 00  |.ELF............|
00000010  02 00 3e 00 01 00 00 00  78 00 40 00 00 00 00 00  |..>.....x.@.....|
00000020  40 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |@...............|
00000030  00 00 00 00 40 00 38 00  01 00 00 00 00 00 00 00  |....@.8.........|
00000040  01 00 00 00 05 00 00 00  00 00 00 00 00 00 00 00  |................|
00000050  00 00 40 00 00 00 00 00  00 00 40 00 00 00 00 00  |..@.......@.....|
00000060  cf 00 00 00 00 00 00 00  cf 00 00 00 00 00 00 00  |................|
00000070  00 10 00 00 00 00 00 00  6a 0e 90 90 90 68 bc 00  |........j....h..|
00000080  40 00 e8 10 00 00 00 48  83 c4 10 bb 00 00 00 00  |@......H........|
00000090  b8 01 00 00 00 cd 80 55  90 90 90 90 48 89 e5 90  |.......U....H...|
000000a0  90 48 8b 55 18 48 8b 4d  10 bb 01 00 00 00 b8 04  |.H.U.H.M........|
000000b0  00 00 00 cd 80 48 89 ec  90 90 5d c3 48 65 6c 6c  |.....H....].Hell|
000000c0  6f 2c 20 77 6f 72 6c 64  21 0a 62 79 65 21 0a     |o, world!.bye!.|
000000cf
```

This is an early release, so likely contains bugs, could delete your hard-drive, etc. etc.

Hope you like it, any patches are very welcome!
