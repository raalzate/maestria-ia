%! comment: This program demonstrates the creation and concurrent execution of multiple threads in Oz.

thread %! comment: Starts the first new thread.
   {Show 'Hola desde el hilo 1'} %! comment: This thread prints 'Hola desde el hilo 1' to the output.
end
thread %! comment: Starts the second new thread. These threads will run concurrently.
   {Show 'Hola desde el hilo 2'} %! comment: This thread prints 'Hola desde el hilo 2' to the output.
end