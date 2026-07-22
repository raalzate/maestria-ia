%! comment: This program demonstrates concurrent Fibonacci sequence generation and consumption using threads in Oz.

declare Fib %! comment: Declares a variable 'Fib' to hold the Fibonacci sequence (a stream).
proc {GenFib N Prev Curr} %! comment: Defines a procedure to generate the Fibonacci sequence.
   if N > 0 then %! comment: If N is greater than 0, continue generating.
      Fib = Curr | {GenFib N-1 Curr (Prev+Curr)} %! comment: Constructs the stream: current number is the head, and the tail is the recursive call with updated previous and current numbers.
   else %! comment: Base case: If N is 0, the stream ends.
      Fib = nil %! comment: The stream is nil (empty).
   end
end

%! comment: This thread generates the Fibonacci sequence without blocking the environment.
thread {GenFib 10 0 1} end %! comment: Starts a new thread to generate the first 10 Fibonacci numbers, starting with 0 and 1.

%! comment: Another thread to consume and display the Fibonacci numbers.
thread %! comment: Starts another new thread.
   {For Fib proc {$ X} {Show X} end} %! comment: Iterates through the 'Fib' stream, showing each number X.
end