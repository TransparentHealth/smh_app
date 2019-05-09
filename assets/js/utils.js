const axios = require('axios')

function generateRandomString () {
  const alphabetArray = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l',
    'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']

  let randomString = ''
  for (let i = 0; i < 10; i++) {
    const randomNumber = Math.floor(Math.random() * 25)
    randomString += alphabetArray[randomNumber]
  }
  return randomString
}

function toggleForm (elements) {
  // takes a collection of elements on a page and adds or removes the class, 'hide'
  // depending on whether the element already contains this class.
  for (const i in elements) {
    if (elements[i].classList) {
      if (elements[i].classList.contains('hide')) {
          elements[i].classList.remove('hide')
      } else {
          elements[i].classList.add('hide')
      }
    }
  }
}

// exports
module.exports.generateRandomString = generateRandomString
module.exports.toggleForm = toggleForm