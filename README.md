## What is this repository?


This repository is a playground where I play with interpreters using [_RPython_](http://rpython.readthedocs.io/en/latest/getting-started.html).

----


Currently, this is some kind of lisp interpreter. The JIT is not fully implemented.

I'm experimenting with some stupid frameless bytecode interpreter.
The idea here is to compile everything into a single bytecode string,
and interpret everything in a single loop, without using python's
recursion when a function call is encountered (in difference with rpython's example interpreter).

Since we won't recurse in our python code, we don't allocate a new frame.

So... at the moment, there is not things like "scopes". It seems easily
to implement, using python recursion.


```python
def execute(frame, bc):
    [...]
    while True:
        [...]
        elif c == bytecode.CALL:
          # function call
          # implementation here
          new_frame = create_frame()
          # I'm willing to avoid recursion here
          r = execute(new_frame, bc)
          [...]
```

## How to compile:

You'll need the RPython toolchain.

Pipe your code to targetnolst-c after rpython's compilation



## Restrictions/bugs/accidental features:


- It don't check your code, won't look for missing/to many arguments when calling
  a function. Most of the time, the runtime will crash. But sometimes, when the stack
  is cooperative, you'll get very _strange behaviors_

- functions does not really return, sometimes. It's currently unclear for me why
  it seems to work most of the time, but not when I nest calls.
  I think I have to debug some _S-Expression_ bytecode's generation.

  A function return value should be bound to a variable to allow
  its usage. If not, it will crash when unpacking function's arguments
  from the stack.

- local variables are leaking. Did I say "scope"? There is no scope!
   Wait... did I say local variables? EVERYONE'S SCOPE IS EVERYONE'S SCOPE!

- a deep recursion fastly blows memory.


## Why I an doing this


It's obvious that I can't do better than BEAM or the JVM alone, with my
poor knowledge on the subject.
I'm essentially doing this for learning - I'm a Python developer focused on
code's performance. I was impressed by the [Pypy project](http://pypy.org/),
and was willing to learn / understand what's going on in a bytecode
interpreter.
Using RPython's toolchain allows me to do that with the language I'm the most
confortable with. It is also a gain of speed, since it provides lot of libraries
to implement a language from scratch - from EBNF parsing to JIT hints.


## What is working so far

_May include regressions. A lot!_


#### Integers and addition

```lisp
(def r 1234)
(print r)
(print (add r 1212))
```

#### Lambda/functions (first class values)

```lisp
(def inc
     (lambda (x)
       (add x 1)))

(print (inc 123))
```

#### Function (poor) definition and nested calls/definitions

```lisp

(def result 12345)

(def myfunc2q
     (lambda ()
       (do
           (def mysubfunc
                (lambda (x)
                  (do
                      (print 666)
                      (print x))))
           (mysubfunc result))))


(myfunc2q)
```

### Recursion, "if statement"

```lisp
(def inc
     (lambda (x)
       (add x 1)))


(def recfunc
     (lambda (x)
       (do
           (print x)
           (if (< x 10)
               (do
                   (def nx (inc x))
                   (recfunc nx))))))


(recfunc 0)
```
