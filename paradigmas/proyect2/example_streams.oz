%! comment: This program demonstrates the use of streams for inter-thread communication in Oz.

declare S %! comment: Declares a variable 'S' which will represent our stream.
thread %! comment: Starts a new thread.
   S = 1|2|3|nil %! comment: This thread 'publishes' values (1, 2, 3) to the stream 'S'. 'nil' marks the end of the stream.
end
thread %! comment: Starts another new thread.
   {For S proc {$ X} {Show X} end} %! comment: This thread 'consumes' the values from the stream 'S', displaying each value X using {Show X}.
end
thread
   {For S proc {$ X} {Show X} end} % El hilo 'consume' los valores
end