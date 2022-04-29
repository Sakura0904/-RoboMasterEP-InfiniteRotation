#include <STC15.h>
// ���峣�õ����
typedef     unsigned char   u8;
typedef     unsigned int    u16;
typedef     unsigned long   u32;

#define S1_S0 0x40
#define S1_S1 0x80
#define FOSC 11059200L
#define BAUD 115200//������
unsigned char WORD;
unsigned char busy;

void send_byte(unsigned char by);
void SendString(unsigned char *s);//�����ַ���

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

//UART�жϷ������
void Uart() interrupt 4 using 1{
	if(RI)
	{
		RI=0;        //���RIλ 
		WORD=SBUF; //�õ����յ���
		SBUF=WORD;  //���õ����ַ����ͻظ��Լ�
	}
}
 
//�����ַ���
void SendString(unsigned char *p){       
	while(*p!= '\0'){
		send_byte(*p);
		p++;
	}
	SBUF = 0;
}
/*����һ���ַ�*/
void send_byte(unsigned char by){

SBUF = by;
while(!TI);//�ȴ��������
TI = 0;    
}
//ͨ�Ŵ����л�
void UART_Init(){

    SCON=0x50;                   //8λ�ɱ䲨����
    T2L=(65536-(FOSC/4/BAUD)); //���ò�������װֵ
    T2H=(65536-(FOSC/4/BAUD))>>8;
    AUXR=0x14;                   //T2Ϊ1Tģʽ����������ʱ��2
    AUXR|=0x01;                   //ѡ��ʱ��2Ϊ����1�Ĳ����ʷ�����
    ES=1;
    EA=1;
    //�ɱ�Ĳ�����ż���ᷢ������
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
