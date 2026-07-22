%! comment: This program demonstrates how to recursively sum the elements of a list in Oz.

%! comment: Example: Sum elements of a list recursively
fun {SumList L} %! comment: Defines a function 'SumList' that takes a list L as input.
   case L of nil then 0 %! comment: Base case: If the list is empty (nil), the sum is 0.
   [] [H|T] then H + {SumList T} %! comment: Recursive case: If the list is not empty, it deconstructs into a Head (H) and a Tail (T).
   end %! comment: The sum is the Head plus the recursive sum of the Tail.
end

{Show {SumList [1 2 3 4]}} %! comment: Calls the SumList function with the list [1 2 3 4] and displays the result (which is 10).