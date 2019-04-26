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

function getUserData (val) {
  return axios.get('/org/org-member-api').then( response => {
    const members = response.data.filter(
        user => {
        const name = user.name.toLowerCase()
          const email = user.email.toLowerCase()
          return name.includes(val) || email.includes(val)
        }
      )
      return members.sort((a, b) => a.family_name.localeCompare(b.family_name))
  })
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
module.exports.getUserData = getUserData
module.exports.toggleForm = toggleForm