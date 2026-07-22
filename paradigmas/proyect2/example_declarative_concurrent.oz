%! comment: This program demonstrates the declarative concurrent paradigm in Oz.
%! comment: It uses dataflow variables and threads to achieve concurrent execution where data dependencies dictate the flow.

declare X %! comment: Declares a dataflow variable X. Initially, X is unbound.

thread %! comment: Thread 1: This thread will produce a value for X.
   {Delay 2000} %! comment: Simulates some work with a 2-second delay.
   X = 'Hola Concurrente!' %! comment: Binds the value 'Hola Concurrente!' to X. This operation is atomic.
end

thread %! comment: Thread 2: This thread will consume the value of X.
   {Show X} %! comment: This operation will block until X is bound by Thread 1.
end

%! comment: The system will automatically handle the synchronization: Thread 2 waits for X to be bound by Thread 1
%! comment: before it can proceed to display its value. This is declarative dataflow concurrency.