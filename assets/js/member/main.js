const utils = require('./../utils')

function toggleEditMember () {
    const form_elements = document.getElementsByClassName('form_element')
    utils.toggleForm(form_elements)

    const read_only_elements = document.getElementsByClassName('read_only_element')
    utils.toggleForm(read_only_elements)
}

// exports
module.exports.toggleEditMember = toggleEditMember
