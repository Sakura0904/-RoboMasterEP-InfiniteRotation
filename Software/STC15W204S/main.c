#include <STC15.h>
// 定义常用的语句
typedef     unsigned char   u8;
typedef     unsigned int    u16;
typedef     unsigned long   u32;

#define S1_S0 0x40
#define S1_S1 0x80
#define FOSC 11059200L
#define BAUD 115200//波特率
unsigned char WORD;
unsigned char busy;

void send_byte(unsigned char by);
void SendString(unsigned char *s);//发送字符串

void UART_Init();
void delay1s();

void main(){
	UART_Init();

	SendString("command;");while(SBUF != 0);
	SendString("robot mode free;");while(SBUF != 0);
	SendString("gimbal push attitude on;");while(SBUF != 0);
	SendString("game_msg on;");while(SBUF != 0);
	SendString("chassis wheel w1 300 w2 -300 w3 -300 w4 300;");while(SBUF != 0);
	//SendString("command;robot mode free;gimbal push attitude on;game_msg on;chassis wheel w1 300 w2 -300 w3 -300 w4 300;");
	
	while (1);
}

//UART中断服务程序
void Uart() interrupt 4 using 1{
	if(RI)
	{
		RI=0;        //清除RI位 
		WORD=SBUF; //得到接收的信
		SBUF=WORD;  //将得到的字符发送回给自己
	}
}
 
//发送字符串
void SendString(unsigned char *p){       
	while(*p!= '\0'){
		send_byte(*p);
		p++;
	}
	SBUF = 0;
}
/*发送一个字符*/
void send_byte(unsigned char by){

SBUF = by;
while(!TI);//等待发送完毕
TI = 0;    
}
//通信串口切换
void UART_Init(){

    SCON=0x50;                   //8位可变波特率
    T2L=(65536-(FOSC/4/BAUD)); //设置波特率重装值
    T2H=(65536-(FOSC/4/BAUD))>>8;
    AUXR=0x14;                   //T2为1T模式，并启动定时器2
    AUXR|=0x01;                   //选择定时器2为串口1的波特率发生器
    ES=1;
    EA=1;
    //可变的波特率偶尔会发生乱码
}
void delay1s() {
	unsigned char i, j, k;
	i = 26;
	j = 60;
	k = 1000;
	do {
		do {
			while (--k);
		}
		while (--j);
	}
	while (--i);
}
