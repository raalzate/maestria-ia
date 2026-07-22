% Punto 4: Fibonacci usando celdas
declare
fun {Fibo N}
   if N < 2 then 1
   else
      Prev = {NewCell 1}
      Curr = {NewCell 1}
      I = {NewCell 2}
   in
      for while:(@I =< N) do
         local Temp = @Curr in
            Curr := @Prev + @Curr
            Prev := Temp
         end
         I := @I + 1
      end
      @Curr
   end
end

{Show {Fibo 0}}   % 1
{Show {Fibo 1}}   % 1
{Show {Fibo 2}}   % 2
{Show {Fibo 5}}   % 8
{Show {Fibo 10}}  % 89
