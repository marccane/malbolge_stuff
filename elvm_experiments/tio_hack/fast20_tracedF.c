
// Loosely based on Matthias Lutter's public domain Malbolge Unshackled interpreter.
// Define `MEMORY' to minimise memory usage at the expense of speed (unaligned loads).
// Build with GCC.

#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <string.h>

const char* translation = "5z]&gqtyfr$(we4{WP)H-Zn,[%\\3dL+Q;>U!pJS72Fh"
        "OA1CB6v^=I_0/8|jsb9m<.TVac`uY*MK'X~xDl}REokN:#?G\"i@";

typedef struct Word {
    #ifndef MEMORY
        unsigned int area;
        unsigned int high;
        unsigned int low;
    #else
        unsigned char area;
        unsigned short high;
        unsigned short low;
    #endif
} Word;

static inline uint16_t crazy_low(uint16_t a, uint16_t d) {
    const uint16_t crz[] = { 1, 0, 0, 1, 0, 2, 2, 2, 1 };
    uint16_t result = 0; uint16_t k = 1;
    for(char pos = 0; pos < 10; pos++) {
        result += k * crz[(a % 3) + 3 * (d % 3)];
        a /= 3; d /= 3; k *= 3;
    }
    return result;
}

static inline Word zero() {
    Word result = {0, 0, 0};
    return result;
}

static inline Word increment(Word d) {
    d.low++;
    if (d.low >= 59049) {
        d.low = 0;
        d.high++;
    }
    return d;
}

static inline Word decrement(Word d) {
    if (d.low == 0) {
        d.low = 59048;
        d.high--;
    }else{
        d.low--;
    }
    return d;
}

static inline Word crazy(Word a, Word d) {
    Word output;
    unsigned int crz[] = {1,0,0,1,0,2,2,2,1};
    output.area = crz[a.area+3*d.area];
    output.high = crazy_low(a.high, d.high);
    output.low = crazy_low(a.low, d.low);
    return output;
}

static inline Word rotate_r(Word d) {
    unsigned int carry_h = d.high % 3;
    unsigned int carry_l = d.low % 3;
    d.high = 19683 * carry_l + ((unsigned int) d.high) / 3;
    d.low = 19683 * carry_h + ((unsigned int) d.low) / 3;
    return d;
}

static unsigned int last_initialized;

static inline Word* ptr_to(Word** mem[], Word d) {
    if ((mem[d.area])[d.high]) {
        return &(((mem[d.area])[d.high])[d.low]);
    }
    (mem[d.area])[d.high] = (Word*)malloc(59049 * sizeof(Word));
    Word repitition[6];
    repitition[(last_initialized-1) % 6] =
            ((mem[0])[(last_initialized-1) / 59049])
                [(last_initialized-1) % 59049];
    repitition[(last_initialized) % 6] =
            ((mem[0])[last_initialized / 59049])
                [last_initialized % 59049];
    #pragma GCC unroll 6
    for (unsigned int i=0;i<6;i++) {
        repitition[(last_initialized+1+i) % 6] =
                crazy(repitition[(last_initialized+i) % 6],
                    repitition[(last_initialized-1+i) % 6]);
    }
    unsigned int offset = (59049*((unsigned int)d.high)) % 6;
    for(unsigned int i = 0; i < 59049; i++) {
        ((mem[d.area])[d.high])[i] = repitition[(i+offset)%6];
    }
    return &(((mem[d.area])[d.high])[d.low]);
}

static inline Word* ptr_toz(Word** mem[], Word d) {
    if (!(mem[d.area])[d.high])
        (mem[d.area])[d.high] = (Word*)malloc(59049 * sizeof(Word));
    
    return &(((mem[d.area])[d.high])[d.low]);
}

static inline unsigned char get_instruction(Word** mem[], Word c) {
    Word* instr = ptr_to(mem, c);
    unsigned int instruction = instr->low;
    instruction = (instruction+((unsigned int) c.low) + 59049 * ((unsigned int) c.high)
            + (c.area==1?52:(c.area==2?10:0)))%94;
    return instruction;
}

__attribute((flatten)) int main(int argc, char* argv[]) {
    Word** memory[3];
    int j;
    #pragma GCC unroll 3
    for (unsigned char i=0; i<3; i++) {
        memory[i] = (Word**)malloc(59049 * sizeof(Word*));
        for (j=0; j<59049; j++) {
            (memory[i])[j] = 0;
        }
    }
    Word a, c, d;
    FILE* file = fopen(argv[1],"rb");
    fseek(file, 0, SEEK_END);
    unsigned int size = ftell(file);
    rewind(file);
    a = zero();
    c = zero();
    d = zero();
    while(1) {
        if(__builtin_expect(size > 16, 1)) {
            char data[16];
            fread(data, 1, 16, file);

            #pragma GCC unroll 16
            for(int i = 0; i < 16; i++) {
                Word* cell = ptr_toz(memory, d);
                (*cell) = zero();
                cell->low = data[i];
                if (cell->low != ' ' && cell->low != '\r' && cell->low != '\n')
                    d = increment(d);
            }
            
            size -= 16;
        } else if(size > 2) {
            char data[2];
            fread(data, 1, 2, file);

            #pragma GCC unroll 2
            for(int i = 0; i < 2; i++) {
                Word* cell = ptr_toz(memory, d);
                (*cell) = zero();
                cell->low = data[i];
                if (cell->low != ' ' && cell->low != '\r' && cell->low != '\n')
                    d = increment(d);
            }
            
            size -= 2;
        } else {
            Word* cell = ptr_toz(memory, d);
            (*cell) = zero();
            fread(&cell->low,1,1,file);
            if (cell->low != ' ' && cell->low != '\r' && cell->low != '\n')
                d = increment(d);
            break;
        }
    }
    fclose(file);
    for(; d.low != 59048; d = increment(d)) {
        *ptr_toz(memory, d) = crazy(*ptr_toz(memory, decrement(d)),
                *ptr_toz(memory, decrement(decrement(d))));
    }
    last_initialized = 59047 + 59049*((unsigned int) d.high);
    d = zero();

    while (1) {
        unsigned char instruction = get_instruction(memory, c);
        { static FILE* tf = 0; static long tn = 0; static long tmax = -1;
          if (!tf) { const char* p = getenv("F20_TRACE"); if (p) tf = fopen(p, "w");
                     const char* m = getenv("F20_TRACE_MAX"); tmax = m ? atol(m) : 2000000; }
          if (tf) { unsigned int pos = (c.low + 59049u*c.high + (c.area==1?52u:(c.area==2?10u:0u))) % 564;
                    fprintf(tf, "%ld %u %u\n", tn, pos, (unsigned)instruction);
                    if (++tn >= tmax) { fclose(tf); exit(42); } } }
        switch (instruction){
            case 4:
                if (getenv("F20_JLOG")) { Word v = *ptr_to(memory,d);
                    fprintf(stderr, "JMP d=(%u,%u,%u) val=(%u,%u,%u)\n",
                            d.area, d.high, d.low, v.area, v.high, v.low); }
                c = *ptr_to(memory,d);
                break;
            case 5:
                if (!a.area) {
                    putchar((char)(((unsigned int) a.low) + 59049*((unsigned int) a.high)));
                    fflush(stdout);
                } else {
                    putchar('\n');
                }
                break;
            case 23:
                a = zero();
                a.low = getchar();
                if (a.low == EOF) {
                    a.low = 59048;
                    a.high = 59048;
                    a.area = 2;
                }else if (a.low == '\n'){
                    a.low = 59047;
                    a.high = 59048;
                    a.area = 2;
                }
                break;
            case 39:
                a = (*ptr_to(memory,d)
                        = rotate_r(*ptr_to(memory,d)));
                { static long m39 = 0; m39++;
                  if (getenv("F20_VLOG")) fprintf(stderr, "R %ld %u %u\n", m39, a.area, a.low); }
                break;
            case 40:
                d = *ptr_to(memory,d);
                break;
            case 62:
                { static long n62 = 0; n62++;
                  if (getenv("F20_JLOG") && d.area != 0) { Word v = *ptr_to(memory,d);
                    fprintf(stderr, "OPR n62=%ld d=(%u,%u,%u) mem_in=(%u,%u,%u)\n",
                            n62, d.area, d.high, d.low, v.area, v.high, v.low); } }
                a = (*ptr_to(memory,d)
                        = crazy(a, *ptr_to(memory,d)));
                { static long m62 = 0; m62++;
                  if (getenv("F20_VLOG")) fprintf(stderr, "C %ld %u %u\n", m62, a.area, a.low); }
                break;
            case 81:
                return 0;
            default:
                break;
        }

        Word* mem_c = ptr_to(memory, c);
        mem_c->low = translation[mem_c->low - 33];

        c = increment(c);
        d = increment(d);
    }
    return 0;
}
