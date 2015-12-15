ArrayList<Dot> dots;

class Dot {
  int x, r, g, b;
  Dot (int pos, int red, int green, int blue){
    x = pos;
    r = red;
    g = green;
    b = blue;
  }
  void update(){
    x = x + 1;
    if (x > 150){
      x = 0;
    }
  }
}

void setup() {
  size(50,755);
  dots = new ArrayList<Dot>();
  int slen = 70;
  for (int i=0; i<slen; i++){
    dots.add(new Dot(i,255,255 - (255/slen)*i, 0));
  }
  background(125);
  fill(255);
  for (int i=0; i<150; i++){
    ellipse(25, 5+i*5, 5, 5);
  }
}

void draw() {
  fill(255);
  for (int i=0; i<150; i++){
    ellipse(25, 5+i*5, 5, 5);
  }
  for (Dot d : dots){
    fill(d.r, d.g, d.b);
    ellipse(25, 5+d.x*5, 5, 5);
    d.update();
  }

}
