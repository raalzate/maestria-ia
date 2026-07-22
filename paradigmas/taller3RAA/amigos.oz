% Punto 6: Amigos y dinero - PagoDeuda
declare

% Verifica si dos personas son amigas
fun {SonAmigos Amistades I J}
   case Amistades
   of nil then false
   [] (A#B)|T then
      if (A==I andthen B==J) orelse (A==J andthen B==I) then true
      else {SonAmigos T I J}
      end
   end
end

% Encuentra los componentes conexos del grafo de amistades
% Usa BFS con celdas para encontrar el componente de un nodo
fun {ComponenteConexo Amistades N Inicio Visitado}
   Cola = {NewCell [Inicio]}
   Componente = {NewCell [Inicio]}
in
   (Visitado.Inicio) := true
   for while:(@Cola \= nil) do
      local Actual = @Cola.1 in
         Cola := @Cola.2
         for K in 1..N do
            if @(Visitado.K) == false andthen {SonAmigos Amistades Actual K} then
               (Visitado.K) := true
               Cola := {Append @Cola [K]}
               Componente := K | @Componente
            end
         end
      end
   end
   @Componente
end

fun {PagoDeuda Amistades Deudas}
   N = {Width Deudas}
   Visitado = {MakeTuple vis N}
   Result = {NewCell true}
in
   % Inicializar visitados
   for I in 1..N do
      Visitado.I = {NewCell false}
   end
   % Para cada componente conexo, la suma de deudas debe ser 0
   for I in 1..N do
      if @(Visitado.I) == false then
         local
            Comp = {ComponenteConexo Amistades N I Visitado}
            SumaComp = {NewCell 0}
         in
            for C in Comp do
               SumaComp := @SumaComp + Deudas.C
            end
            if @SumaComp \= 0 then
               Result := false
            end
         end
      end
   end
   @Result
end

{Browse {PagoDeuda [1#2 2#3 4#5] [100 ~75 ~25 ~42 42]}}   % true
{Browse {PagoDeuda [1#3 2#4] [15 20 ~10 ~25]}}             % false
