% Punto 5: BubbleSort usando celdas
declare
fun {BubbleSort L}
   Arr = {List.toTuple arr L}
   N = {Width Arr}
   A = {NewCell {Record.toList Arr}}
in
   if N =< 1 then L
   else
      local
         Cells = {MakeTuple cells N}
      in
         % Inicializar celdas con los valores de la lista
         for K in 1..N do
            Cells.K = {NewCell Arr.K}
         end
         % BubbleSort con celdas
         for I in 1..(N-1) do
            for J in 1..(N-I) do
               if @(Cells.J) > @(Cells.(J+1)) then
                  local Temp = @(Cells.J) in
                     (Cells.J) := @(Cells.(J+1))
                     (Cells.(J+1)) := Temp
                  end
               end
            end
         end
         % Construir lista resultado
         local
            Result = {NewCell nil}
         in
            for K in N..1;~1 do
               Result := @(Cells.K) | @Result
            end
            @Result
         end
      end
   end
end

{Show {BubbleSort [5 3 8 1 2]}}     % [1 2 3 5 8]
{Show {BubbleSort [9 7 5 3 1]}}     % [1 3 5 7 9]
{Show {BubbleSort [1]}}             % [1]
{Show {BubbleSort nil}}             % nil
