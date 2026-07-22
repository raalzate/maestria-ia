%! comment: This program demonstrates pattern matching using the 'case' statement in Oz, applied to lists and records.

declare L %! comment: Declares a variable L for a list.
L = [1 2 3] %! comment: Initializes L with a list of integers.

case L of [H|T] then %! comment: Pattern matches the list L. If L is not empty, it binds its head to H and its tail to T.
   {Show H} %! comment: Displays the head of the list (1).
   {Show T} %! comment: Displays the tail of the list ([2 3]).
else %! comment: If the list L does not match the pattern (i.e., it's empty),
   {Show 'Lista vacia'} %! comment: it displays 'Lista vacia'.
end

declare P %! comment: Declares a variable P for a record.
P = persona(nombre:"Pedro" edad:25) %! comment: Initializes P with a record representing a person.
case P of persona(nombre:N edad:E) then %! comment: Pattern matches the record P. It binds the value of the 'nombre' field to N and 'edad' to E.
   {Show N} %! comment: Displays the name (Pedro).
   {Show E} %! comment: Displays the age (25).
end