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
module.exports.toggleForm = toggleForm