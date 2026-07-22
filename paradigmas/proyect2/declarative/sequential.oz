declare
  fun {Factorial N}
    if N == 0 then 1
    else N * {Factorial N-1}
    end
  end

  fun {Fibonacci N}
    if N =< 1 then N
    else {Fibonacci N-1} + {Fibonacci N-2}
    end
  end
in
  {Browse {Factorial 5}}   % Muestra 120
  {Browse {Fibonacci 10}}  % Muestra 55
