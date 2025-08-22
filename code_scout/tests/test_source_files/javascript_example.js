const GLOBAL_VAR = "hello";

class Animal {
  constructor(name) {
    this.name = name;
  }

  speak() {
    return `${this.name} makes a noise.`;
  }
}

class Dog extends Animal {
  static species = "Canis familiaris";

  constructor(name, breed) {
    super(name);
    this.breed = breed;
  }

  bark() {
    return `${this.name} barks!`;
  }

  get info() {
    return `${this.name} is a ${this.breed}.`;
  }

  set newBreed(breed) {
    this.breed = breed;
  }

  async fetchData() {
    const response = await Promise.resolve("data");
    return response;
  }
}

function regularFunction(a, b) {
  let result = a + b;
  function innerFunction(x) {
    return x * 2;
  }
  return innerFunction(result);
}

const arrowFunction = (x, y) => {
  const temp = x * y;
  return temp / 2;
};

export class Utility {
  static helper() {
    return "I'm a helper.";
  }
}

export function exportedFunction() {
  return "This is exported.";
}