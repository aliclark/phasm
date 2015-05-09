# phasm
Phasm is a generic assembler or binary generation language.

This is an early release, so the error reporting is woefully bad, the
compiler likely contains bugs, and a lot of features are yet to be
written. But it does work!

An example [hello.psm](https://github.com/aliclark/phasm-hello/blob/master/hello.psm):

```ruby
(elf, proc, sys, util) -> {
    data = {}
    bss  = {}

    rodata = {
        hello_world = util.utf8("Hello, world!\n")
        :hello_world_addr: hello_world
    }

    text = (rodata, data, bss) -> {
        :print: proc.sub2((addr, size) -> {
            sys.write(sys.fd_stdout, addr, size)
        })

        :start: {
            proc.call2(print, rodata.hello_world_addr, rodata.hello_world.size)
            sys.exit(0)
        }
    }

    elf.linux_x64(rodata, data, bss, text)
}
```

And [hello-linux-x64.psm](https://github.com/aliclark/phasm-hello/blob/master/hello-linux-x64.psm):

```ruby
#!/usr/bin/env phasm

num      = Import("gh:aliclark/phasm-std/0.3/num.py")
str      = Import("gh:aliclark/phasm-std/0.3/str.py")
bin_base = Import("gh:aliclark/phasm-std/0.3/bin.py")
asm_base = Import("gh:aliclark/phasm-std/0.3/asm_x64.py")

abs_bin  = Import("gh:aliclark/phasm-std/0.3/bin.psm")
abs_asm  = Import("gh:aliclark/phasm-std/0.3/asm-x64.psm")
abs_elf  = Import("gh:aliclark/phasm-std/0.3/elf.psm")
abs_proc = Import("gh:aliclark/phasm-std/0.3/proc-x64.psm")
abs_sys  = Import("gh:aliclark/phasm-std/0.3/syscall-linux-x64.psm")
abs_util = Import("gh:aliclark/phasm-std/0.3/util.psm")

abs_hello = Import("gh:aliclark/phasm-hello/0.1/hello.psm")

bin  = abs_bin(bin_base)
asm  = abs_asm(num, bin, asm_base)
elf  = abs_elf(num, str, bin)
proc = abs_proc(asm)
sys  = abs_sys(bin, asm)
util = abs_util(str, asm, sys)

abs_hello(elf, proc, sys, util)
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

# download the code from the internet and run it.
# the first run will take some time to fetch
phasm <(echo 'Import("gh:aliclark/phasm-hello/0.1/hello-linux-x64.psm")')
```

This compiles and runs a 202 byte ELF binary:

```
00000000  7f 45 4c 46 02 01 01 03  00 00 00 00 00 00 00 00  |.ELF............|
00000010  02 00 3e 00 01 00 00 00  9d 00 40 00 00 00 00 00  |..>.......@.....|
00000020  40 00 00 00 00 00 00 00  00 00 00 00 00 00 00 00  |@...............|
00000030  00 00 00 00 40 00 38 00  01 00 00 00 00 00 00 00  |....@.8.........|
00000040  01 00 00 00 05 00 00 00  00 00 00 00 00 00 00 00  |................|
00000050  00 00 40 00 00 00 00 00  00 00 40 00 00 00 00 00  |..@.......@.....|
00000060  ca 00 00 00 00 00 00 00  ca 00 00 00 00 00 00 00  |................|
00000070  00 10 00 00 00 00 00 00  55 90 90 90 90 48 89 e5  |........U....H..|
00000080  90 90 48 8b 55 18 48 8b  4d 10 bb 01 00 00 00 b8  |..H.U.H.M.......|
00000090  04 00 00 00 cd 80 48 89  ec 90 90 5d c3 6a 0e 90  |......H....].j..|
000000a0  90 90 68 bc 00 40 00 e8  cc ff ff ff 48 83 c4 10  |..h..@......H...|
000000b0  bb 00 00 00 00 b8 01 00  00 00 cd 80 48 65 6c 6c  |............Hell|
000000c0  6f 2c 20 77 6f 72 6c 64  21 0a                    |o, world!.|
000000ca
```

This is an early release, so likely contains bugs, could delete your hard-drive, etc. etc.

Hope you like it, any patches are very welcome!
