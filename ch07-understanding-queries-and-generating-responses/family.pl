parent(tom, liz).
parent(bob, ann).
parent(bob, pat).
parent(pat, jim).

male(tom).
male(bob).
male(jim).
female(pam).
female(liz).
female(pat).
female(ann).

mother(X) :- parent(X, _), female(X).
father(X) :- parent(X, _), male(X).
grandparent(X) :- parent(X, Y), parent(Y, _).
sisters(X, Y) :- parent(Z, X), parent(Z, Y), female(X), female(Y),
                 X @< Y.

