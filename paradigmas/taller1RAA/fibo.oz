declare
% fibo.oz - Autor: Raul A. Alzate
% fib(n) = 1          si n < 2
% fib(n) = fib(n-1) + fib(n-2)   si n >= 2

% --- Version 1: Recursiva intuitiva (computacion recursiva) ---
% Genera un arbol de llamadas de tamano O(2^N).
% La suma pendiente en la pila semantica impide aplicar TCO.
% En este computador corre en tiempo razonable hasta aproximadamente N = 35.
fun {FiboRec N}
   if N < 2 then 1
   else {FiboRec N-1} + {FiboRec N-2}
   end
end

% --- Version 2: Iterativa con recursion de cola ---
% Estado S = (K, Curr, Prev)
%   Invariante P(K, Curr, Prev): Curr = fib(K) /\ Prev = fib(K-1)
%   S0      = (1, 1, 1)         [K=1, Curr=fib(1)=1, Prev=fib(0)=1]
%   S_{i+1} = (K+1, Curr+Prev, Curr)
%   S_final = (N, fib(N), fib(N-1))
% Progreso: K crece de 1 a N -> se alcanza el estado final en N-1 pasos.
fun {Fibo N}
   fun {FiboAcc K Curr Prev}
      if K == N then Curr
      else {FiboAcc K+1 Curr+Prev Curr}
      end
   end
in
   if N < 2 then 1
   else {FiboAcc 1 1 1}
   end
end

% Verificacion
{Browse {FiboRec 10}}  % Esperado: 89
{Browse {Fibo 10}}     % Esperado: 89

% N maximo para version recursiva (~35)
{Browse {FiboRec 35}}

% Pruebas con version iterativa para valores grandes (N=35)
local N = 35 in
   {Browse {Fibo N+1}}    % Fib(36)
   {Browse {Fibo 10*N}}   % Fib(350)
   {Browse {Fibo 100*N}}  % Fib(3500)
end
