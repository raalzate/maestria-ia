%! comment: This program defines a function to calculate the factorial of a number.

fun {Factorial N} %! comment: Defines the Factorial function that takes an integer N as input.
   if N == 0 then 1 %! comment: Base case: If N is 0, the factorial is 1.
   else N * {Factorial N-1} %! comment: Recursive case: If N is not 0, multiply N by the factorial of N-1.
   end
end

{Show {Factorial 5}} %! comment: Calls the Factorial function with 5 and displays the result (which is 120).