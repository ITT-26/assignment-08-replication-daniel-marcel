const int pt1 = A0;
const int pt2 = A1;
const int pt3 = A2;

void setup() {
  // put your setup code here, to run once:
  Serial.begin(9600);

  pinMode(9, OUTPUT);
  pinMode(10, OUTPUT);
  pinMode(11, OUTPUT);
}

int i = 1;

void loop() {
  int pt1value = analogRead(pt1);
  int pt2value = analogRead(pt2);
  int pt3value = analogRead(pt3);

  int dt = 50;

  delay(dt);
  digitalWrite(9, 1000);
  pt1value = analogRead(pt1);
  pt2value = analogRead(pt2);
  pt3value = analogRead(pt3);
  Serial.print(pt1value);
  Serial.print(", ");
  Serial.print(pt2value);
  Serial.print(", ");
  Serial.println(pt3value);
  delay(dt);
  digitalWrite(9, 0);
  pt1value = analogRead(pt1);
  pt2value = analogRead(pt2);
  pt3value = analogRead(pt3);
  Serial.print(pt1value);
  Serial.print(", ");
  Serial.print(pt2value);
  Serial.print(", ");
  Serial.println(pt3value);
  delay(dt);
  digitalWrite(10, 1000);
  pt1value = analogRead(pt1);
  pt2value = analogRead(pt2);
  pt3value = analogRead(pt3);
  Serial.print(pt1value);
  Serial.print(", ");
  Serial.print(pt2value);
  Serial.print(", ");
  Serial.println(pt3value);
  delay(dt);
  digitalWrite(10, 0);
  pt1value = analogRead(pt1);
  pt2value = analogRead(pt2);
  pt3value = analogRead(pt3);
  Serial.print(pt1value);
  Serial.print(", ");
  Serial.print(pt2value);
  Serial.print(", ");
  Serial.println(pt3value);
  delay(dt);
  digitalWrite(11, HIGH);
  pt1value = analogRead(pt1);
  pt2value = analogRead(pt2);
  pt3value = analogRead(pt3);
  Serial.print(pt1value);
  Serial.print(", ");
  Serial.print(pt2value);
  Serial.print(", ");
  Serial.println(pt3value);
  delay(dt);
  digitalWrite(11, 0);
  pt1value = analogRead(pt1);
  pt2value = analogRead(pt2);
  pt3value = analogRead(pt3);
  Serial.print(pt1value);
  Serial.print(", ");
  Serial.print(pt2value);
  Serial.print(", ");
  Serial.println(pt3value);
  delay(dt);

}
