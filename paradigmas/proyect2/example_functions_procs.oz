%! comment: This program demonstrates the difference between functions and procedures in Oz.

%! comment: Function (returns a value by binding the last argument)
fun {Suma A B} %! comment: Defines a function 'Suma' that takes two arguments, A and B.
   A+B %! comment: The function returns the sum of A and B.
end

%! comment: Procedure (performs an action, does not necessarily return a value)
proc {Imprime X} %! comment: Defines a procedure 'Imprime' that takes one argument, X.
   {Show X} %! comment: Displays the value of X in the Oz environment (browser).
end

% Procedimiento (realiza una acción, no necesariamente regresa un valor)
proc {Imprime X}
   {Show X} % Muestra el valor de X en el navegador (entorno Oz)
end