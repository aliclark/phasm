# phasm
Phasm is a generic assembler or binary generation language that is
thoroughly incomplete, but might be useful at some point.

A very basic example program and how to run it:

```ruby
(std, asm, elf, proc, sys, util) -> {

    bytes = (n) -> std.U(n, 0)
    type = (block) -> WithPosition(0, block)

    rodata = {
        hello_world = util.utf8("Hello, world!\n")
        bye         = util.utf8("bye!\n")

        :hello_world_addr: hello_world
        :bye_addr:         bye

	# TODO: new syntax
        # :hello_world: = util.utf8("Hello, world!\n")
        # :bye:         = util.utf8("bye!\n")
    }

    data = {
        :verbose: std.U(1, 0)
    }

    ptr_new = bytes(8)
    ptr_t = type(ptr_new)

    list_new = {
        :value: ptr_new
        :next:  ptr_new
    }
    # eg. std.sizeof(list_t)
    list_t = type(list_new)

    bss = {
        :counter: bytes(8)
        #:big_obj: bytes(128)
        :my_foo_list: list_new
    }

    text = (rodata, data, bss) -> {
        :start: {
            # TODO: seccomp2 ourselves down to just sys_write and sys_exit

            util.loop(2, {
                proc.call2(print, rodata.hello_world_addr, rodata.hello_world.size)
            })
            proc.call2(print, rodata.bye_addr, rodata.bye.size)

            # XXX: after new syntax:
            # print.call(rodata.bye, rodata.bye.size)

            sys.exit(42)
        }

        :print: proc.sub2({
            asm.mov("rbx", sys.fd_stdout)
            asm.mov("rcx", "[rbp+16]")
            asm.mov("rdx", "[rbp+24]")
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
phasm <(echo 'Import("gh:aliclark/phasm-scratch/master/hello.psm")')
```

This compiles and runs a binary of 279 bytes:

```
00000000  7f 45 4c 46 02 01 01 03  00 00 00 00 00 00 00 00  |.ELF............|
00000010  02 00 3e 00 01 00 00 00  78 00 40 00 00 00 00 00  |..>.....x.@.....|
00000020  40 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |@...............|
00000030  00 00 00 00 40 00 38 00  01 00 00 00 00 00 00 00  |....@.8.........|
00000040  01 00 00 00 05 00 00 00  00 00 00 00 00 00 00 00  |................|
00000050  00 00 40 00 00 00 00 00  00 00 40 00 00 00 00 00  |..@.......@.....|
00000060  17 01 00 00 00 00 00 00  17 01 00 00 00 00 00 00  |................|
00000070  00 10 00 00 00 00 00 00  50 90 90 90 90 b8 00 00  |........P.......|
00000080  00 00 48 83 f8 02 7d 1f  50 90 90 90 90 6a 0e 90  |..H...}.P....j..|
00000090  90 90 68 eb 00 40 00 e8  2a 00 00 00 48 83 c4 10  |..h..@..*...H...|
000000a0  58 48 83 c0 01 eb db 6a  05 90 90 90 68 f9 00 40  |XH.....j....h..@|
000000b0  00 e8 10 00 00 00 48 83  c4 10 bb 2a 00 00 00 b8  |......H....*....|
000000c0  01 00 00 00 cd 80 55 90  90 90 90 48 89 e5 90 90  |......U....H....|
000000d0  bb 01 00 00 00 48 8b 4d  10 48 8b 55 18 b8 04 00  |.....H.M.H.U....|
000000e0  00 00 cd 80 48 89 ec 90  90 5d c3 48 65 6c 6c 6f  |....H....].Hello|
000000f0  2c 20 77 6f 72 6c 64 21  0a 62 79 65 21 0a 00 00  |, world!.bye!...|
00000100  00 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |................|
00000110  00 00 00 00 00 00 00                              |.......|
00000117
```

This is an early release, so likely contains bugs, could delete your hard-drive, etc. etc.

Hope you like it, any patches are very welcome!
