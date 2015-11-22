### Toy C++ editor with REPL for prototyping simple things
This really has nothing to do with REPLs or C++ - this is just a wrapper for 'highlight', 'clang', and varios tools. The REPL is really just a loop over input, with no inline evaluating ; you only evaluate when the actual file is written and python execs clang. 

This is useful for me when I need to check sizes of objects or play with the STL. Since it does produce an actual file on disk, I guess this can be used to create a source code template of some sort. Do what you want with it.

Simple Example

![simple.gif](/img/simple.gif)

A More Complicated Example

![class.gif](/img/class.gif)
