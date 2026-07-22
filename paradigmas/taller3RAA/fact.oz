% Punto 3: Factorial usando celdas
declare
fun {Fact N}
   Result = {NewCell 1}
   I = {NewCell 1}
in
   for while:(@I =< N) do
      Result := @Result * @I
      I := @I + 1
   end
   @Result
end

{Show {Fact 0}}   % 1
{Show {Fact 1}}   % 1
{Show {Fact 5}}   % 120
{Show {Fact 10}}  % 3628800
