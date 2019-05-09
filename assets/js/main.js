const member = require('./member/main')
const utils = require('./utils')
const axios = require('axios')

// ------------------------- search functionality in the header ------------------------- //
const memberSearch = document.getElementById('member-search')
const memberResults = document.getElementById('autocomplete-user-results')
const memberSearchForm = document.getElementById('header-search-form')

function formatListResults (members) {
	return members.map(mem => {
		// `mem.extra_data.picture` does not currently work, but in the future extra_data should include this picture url from the vmi server
		return '<li class="user-link"><a href="/member/' + mem.id + '"><img src="' + mem.extra_data.picture + '" class="mr-3">' + mem.user.first_name + ' ' + mem.user.last_name +'</a></li>'
	}).join('')
}

function getUserData (val) {
	return axios.get('/org/org-member-api').then( response => {
		const members = response.data.filter(
    		member => {

				const first_name = member.user.first_name.toLowerCase()
				const last_name = member.user.last_name.toLowerCase()
    			const email = member.user.email.toLowerCase()
    			return last_name.includes(val) || first_name.includes(val) || email.includes(val)
    		}
    	)
    	return members.sort((a, b) => a.user.last_name.localeCompare(b.user.last_name))
	})
}

function showMemberResults (e) {
	memberResults.classList.remove('hide')
	const val = e.target.value.toLowerCase()
	getUserData(val)
	.then(members => {
    	memberResults.querySelector('.results-title').innerHTML = members.length > 0 ? 'Quick Results' : 'No Results'
    	memberResults.querySelector('.results-list').innerHTML = formatListResults(members)
    	const resultsLinkText = members.length > 0 ? (members.length === 1 ? 'SEE RESULTS' : 'SEE ALL ' + members.length + ' RESULTS') : ''
    	memberResults.querySelector('.all-results').innerHTML = resultsLinkText
	})
}

function hideMemberResults (e) {
	// timeout allows user to click on selection before list disappears
	setTimeout(function(){
		memberResults.classList.add('hide')
	}, 500)
}

function submitMemberSearchForm () {
	memberSearchForm.submit()
}

// ------------------------- member toggle ------------------------- //
const editMember = document.getElementById('edit_member')


// ------------------------- search page results ------------------------- //
const searchContainer = document.getElementById('search-container')
const sortOption = document.getElementById('sortOption')

function populateSearchPage () {
	const term = window.location.search
	const val = term ? term.split('=')[1] : ''
	const response = getUserData(val).then(members => {
		// resorting the order if sortOption changes
		members = sortOption.value === 'A-Z' ? members : members.reverse((a, b) => a.family_name.localeCompare(b.family_name))
		searchContainer.querySelector('.list--formatted').innerHTML = formatListResults(members)
		const forText = val.length !== 0 ? 'FOR "' + val + '"' : ''
		const h2Text = members.length > 0 ? (members.length === 1 ? '1 SEARCH RESULT FOR "' + val +'"' : members.length + ' SEARCH RESULTS ' + forText) : 'NO RESULTS ' + forText
		searchContainer.querySelector('h2').innerHTML = h2Text
	})
}

window.addEventListener('DOMContentLoaded', () => {

	// ------------------------- search functionality in the header ------------------------- //
	if (memberSearch) {
		memberSearch.onkeyup = showMemberResults
		memberSearch.onblur = hideMemberResults
		memberResults.querySelector('.all-results').onclick = submitMemberSearchForm
		memberSearch.name = utils.generateRandomString()
	}

	// ------------------------- member toggle ------------------------- //
	if (editMember) {
	  // if member template is loaded add listener to edit_member element
	  editMember.onclick = member.toggleEditMember
	}

	// ------------------------- search page results ------------------------- //
	if (searchContainer) {
		populateSearchPage()
		sortOption.onchange = populateSearchPage
	}

})
