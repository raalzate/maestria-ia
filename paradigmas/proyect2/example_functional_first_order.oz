%! comment: This program demonstrates a first-order functional paradigm in Oz.
%! comment: Functions are treated as first-class citizens, but we won't pass them as arguments or return them yet.
%! comment: This example focuses on pure functions: they always produce the same output for the same input and have no side effects.

fun {Square N} %! comment: Defines a pure function 'Square' that takes one argument, N.
   N * N %! comment: Returns the square of N. This function has no side effects.
end

declare A
A = 5 %! comment: Declares and binds variable A to 5.

declare Result
Result = {Square A} %! comment: Calls the 'Square' function with A and binds the result to 'Result'.
                    %! comment: The value of A remains unchanged, demonstrating immutability.

{Show Result} %! comment: Displays the result (25).

%! comment: Another call with a different input
{Show {Square 10}} %! comment: Displays the result (100). The function behaves predictably.