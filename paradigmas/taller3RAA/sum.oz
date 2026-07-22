% Punto 2: Suma iterativa de A a B usando celdas
declare
fun {Q A B}
   Sum = {NewCell 0}
   I = {NewCell A}
in
   for while:(@I =< B) do
      Sum := @Sum + @I
      I := @I + 1
   end
   @Sum
end

{Show {Q 1 10}}   % 55
{Show {Q 3 7}}    % 25
{Show {Q 5 5}}    % 5
