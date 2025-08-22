import 'dart:async';

const String APP_NAME = "MyApp";

enum Status {
  active,
  inactive,
  pending,
}

abstract class Shape {
  double get area;
  void display();
}

mixin Logger {
  void log(String message) {
    print("[LOG] $message");
  }
}

class Circle extends Shape with Logger {
  final double radius;
  static const double PI = 3.14159;

  Circle(this.radius) {
    print("hello");
  }

  @override
  double get area => PI * radius * radius;

  @override
  void display() {
    log("Circle with radius $radius and area $area");
  }

  static String getShapeType() {
    return "Circle";
  }

  Future<String> asyncOperation() async {
    await Future.delayed(Duration(milliseconds: 100));
    return "Async operation complete";
  }
}

void topLevelFunction(String message) {
  print("Top-level: $message");
  void nestedFunction() {
    print("Nested function called.");
  }

  nestedFunction();
}

String getFormattedMessage(String msg) => "Formatted: $msg";

Stream<int> countStream(int to) async* {
  for (int i = 1; i <= to; i++) {
    yield i;
  }
}

void main() async {
  var myCircle = Circle(5.0);
  myCircle.display();
  print(Circle.getShapeType());
  print(await myCircle.asyncOperation());
  topLevelFunction("Hello Dart");
  print(getFormattedMessage("Test"));

  await for (var i in countStream(3)) {
    print("Stream value: $i");
  }
}
