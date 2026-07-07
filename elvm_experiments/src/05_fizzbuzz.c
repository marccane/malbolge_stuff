#include <stdio.h>
static void print_num(int n) {
  char buf[8]; int i = 0;
  if (n == 0) { putchar('0'); return; }
  while (n > 0) { buf[i++] = '0' + n % 10; n /= 10; }
  while (i > 0) putchar(buf[--i]);
}
int main() {
  int i;
  for (i = 1; i <= 15; i++) {
    if (i % 15 == 0) { putchar('F'); putchar('B'); }
    else if (i % 3 == 0) putchar('F');
    else if (i % 5 == 0) putchar('B');
    else print_num(i);
    putchar('\n');
  }
  return 0;
}
