%! comment: This program demonstrates a purely declarative sequential paradigm in Oz.
%! comment: It defines a function to calculate the sum of elements in a list using recursion.
%! comment: The result depends only on the input, and there are no side effects.

fun {SumList L} %! comment: Defines a function 'SumList' that takes a list L as input.
   case L of nil then 0 %! comment: Base case: If the list is empty (nil), its sum is 0.
   [] H|T then H + {SumList T} %! comment: Recursive case: If the list is not empty, it's deconstructed into its head (H) and tail (T).
                        %! comment: The sum is the head element plus the recursive sum of the tail.
   end
end

declare MyList
MyList = [1 2 3 4 5] %! comment: Defines a list of numbers.

declare Result
Result = {SumList MyList} %! comment: Calls the SumList function with MyList and binds the result to 'Result'.

{Show Result} %! comment: Displays the final result (15).