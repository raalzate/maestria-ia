% Ejercicio 7: Sincronizacion de hilos con Wait
% terminacion.oz
%
% El problema es que Show puede llamarse antes de que los hilos terminen.
% Se usa {Wait X} para esperar que cada lista este completamente ligada
% antes de invocar Show.

declare L1 L2 L3 L4 in
L1 = [1 2 3]
thread L2 = {Map L1 fun {$ X} {Delay 200} X*X end} end
thread L3 = {Map L1 fun {$ X} {Delay 200} 2*X end} end
thread L4 = {Map L1 fun {$ X} {Delay 200} 3*X end} end

% Esperar que cada lista este completamente ligada (Wait solo espera
% que la variable este ligada; WaitNeeded o recursion para listas completas)
{Wait L2}
{Wait L3}
{Wait L4}
{Show L2#L3#L4}
