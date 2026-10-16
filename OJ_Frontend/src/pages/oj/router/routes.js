import {
  Home,
  Logout,
  NotFound,
  OIRank,
  Problem,
  ProblemList,
  SubmissionDetails,
  SubmissionList
} from '../views'

export default [
  {
    name: 'home',
    path: '/',
    meta: {title: 'Ujian'},
    component: Home
  },
  {
    name: 'logout',
    path: '/logout',
    meta: {title: 'Keluar'},
    component: Logout
  },
  {
    name: 'problem-list',
    path: '/problem',
    meta: {title: 'Soal'},
    component: ProblemList
  },
  {
    name: 'problem-details',
    path: '/problem/:problemID',
    meta: {title: 'Detail Soal'},
    component: Problem
  },
  {
    name: 'submission-list',
    path: '/status',
    meta: {title: 'Pengumpulan'},
    component: SubmissionList
  },
  {
    name: 'submission-details',
    path: '/status/:id/',
    meta: {title: 'Detail Pengumpulan'},
    component: SubmissionDetails
  },
  {
    name: 'oi-rank',
    path: '/oi-rank',
    meta: {title: 'Peringkat OI'},
    component: OIRank
  },
  {
    path: '*',
    meta: {title: '404'},
    component: NotFound
  }
]
