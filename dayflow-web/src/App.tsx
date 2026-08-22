import { useState, useEffect } from 'react';
import { 
  Clock, Calendar, DollarSign, Brain, LogOut, 
  User, Shield, Plus, BarChart2, AlertCircle, AlertTriangle
} from 'lucide-react';
import { 
  AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, 
  ResponsiveContainer, BarChart, Bar
} from 'recharts';
import { api } from './services/api';
import type { UserSession, AttendanceRecord, LeaveRequest, PayrollRecord, AIInsights } from './services/api';

function App() {
  // App States
  const [session, setSession] = useState<UserSession | null>(() => {
    const saved = localStorage.getItem('dayflow_session');
    if (saved) {
      try {
        const parsed = JSON.parse(saved);
        if (parsed && parsed.employee) {
          return parsed;
        }
      } catch (e) {}
      localStorage.removeItem('dayflow_session');
    }
    return null;
  });
  
  const [loginVal, setLoginVal] = useState('admin'); // Default login for hackathon testing
  const [passwordVal, setPasswordVal] = useState('admin');
  const [authError, setAuthError] = useState('');
  const [loading, setLoading] = useState(false);

  // Sign Up states
  const [isSignUp, setIsSignUp] = useState(false);
  const [signUpName, setSignUpName] = useState('');
  const [signUpEmail, setSignUpEmail] = useState('');
  const [signUpPassword, setSignUpPassword] = useState('');
  const [signUpRole, setSignUpRole] = useState<'employee' | 'hr_officer' | 'admin'>('employee');

  // Tab State
  const [activeTab, setActiveTab] = useState<'dashboard' | 'attendance' | 'leaves' | 'payroll' | 'insights'>('dashboard');

  // Business States
  const [attendances, setAttendances] = useState<AttendanceRecord[]>([]);
  const [leaves, setLeaves] = useState<LeaveRequest[]>([]);
  const [payrolls, setPayrolls] = useState<PayrollRecord[]>([]);
  const [insights, setInsights] = useState<AIInsights | null>(null);

  // Check In/Out States
  const [remarks, setRemarks] = useState('');
  const [isCheckedIn, setIsCheckedIn] = useState(false);
  const [todayRecord, setTodayRecord] = useState<AttendanceRecord | null>(null);

  // Action Modals
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [leaveType, setLeaveType] = useState<'sick' | 'casual' | 'earned'>('sick');
  const [leaveStart, setLeaveStart] = useState('');
  const [leaveEnd, setLeaveEnd] = useState('');
  const [leaveError, setLeaveError] = useState('');

  const [showRejectModal, setShowRejectModal] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  // Save session helper
  const saveSession = (userSession: UserSession) => {
    localStorage.setItem('dayflow_session', JSON.stringify(userSession));
    setSession(userSession);
  };

  // Clear session helper
  const clearSession = () => {
    localStorage.removeItem('dayflow_session');
    setSession(null);
    setAttendances([]);
    setLeaves([]);
    setPayrolls([]);
    setInsights(null);
  };

  // Login handler
  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthError('');
    try {
      const data = await api.login(loginVal, passwordVal);
      saveSession(data);
    } catch (err: any) {
      setAuthError(err.message || 'Login failed. Please verify credentials.');
    } finally {
      setLoading(false);
    }
  };

  // Sign Up handler
  const handleSignUp = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setAuthError('');
    try {
      const data = await api.signup(signUpName, signUpEmail, signUpPassword, signUpRole);
      saveSession(data);
    } catch (err: any) {
      setAuthError(err.message || 'Signup failed. User may already exist.');
    } finally {
      setLoading(false);
    }
  };

  // Logout handler
  const handleLogout = async () => {
    try {
      await api.logout();
    } catch (e) {
      console.warn("Server-side logout warning:", e);
    } finally {
      clearSession();
    }
  };

  // Fetch all core business data
  const fetchData = async () => {
    if (!session) return;
    try {
      const attData = await api.getAttendance();
      setAttendances(attData);

      // Infer if employee is checked in today
      const todayStr = new Date().toISOString().split('T')[0];
      const todayLogs = attData.filter(a => a.date === todayStr);
      const activeLog = todayLogs.find(a => a.check_out === null);
      if (activeLog) {
        setIsCheckedIn(true);
        setTodayRecord(activeLog);
      } else {
        setIsCheckedIn(false);
        setTodayRecord(null);
      }

      const leaveData = await api.getLeaves();
      setLeaves(leaveData);

      const payrollData = await api.getPayroll();
      setPayrolls(payrollData);

      if (session.employee.role !== 'employee') {
        const insightData = await api.getAIInsights();
        setInsights(insightData);
      }
    } catch (err) {
      console.error("Error fetching business data:", err);
    }
  };

  useEffect(() => {
    fetchData();
    // Refresh data every 30 seconds for live updates during demo
    const interval = setInterval(fetchData, 30000);
    return () => clearInterval(interval);
  }, [session]);

  // Check-In Action
  const handleCheckIn = async () => {
    setLoading(true);
    try {
      await api.checkIn(remarks);
      setRemarks('');
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to check in.");
    } finally {
      setLoading(false);
    }
  };

  // Check-Out Action
  const handleCheckOut = async () => {
    setLoading(true);
    try {
      await api.checkOut(remarks);
      setRemarks('');
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to check out.");
    } finally {
      setLoading(false);
    }
  };

  // Submit Leave Request
  const handleLeaveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLeaveError('');
    if (!leaveStart || !leaveEnd) {
      setLeaveError("Please specify start and end dates.");
      return;
    }
    setLoading(true);
    try {
      await api.submitLeave(leaveType, leaveStart, leaveEnd);
      setShowLeaveModal(false);
      setLeaveStart('');
      setLeaveEnd('');
      await fetchData();
    } catch (err: any) {
      setLeaveError(err.message || "Failed to submit leave request.");
    } finally {
      setLoading(false);
    }
  };

  // Approve Leave
  const handleLeaveApprove = async (id: number) => {
    if (!confirm("Are you sure you want to approve this leave request?")) return;
    try {
      await api.approveLeave(id);
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to approve leave.");
    }
  };

  // Reject Leave Modal Trigger
  const handleLeaveRejectSubmit = async () => {
    if (!rejectReason) {
      alert("Please provide a rejection reason.");
      return;
    }
    try {
      await api.rejectLeave(showRejectModal!, rejectReason);
      setShowRejectModal(null);
      setRejectReason('');
      await fetchData();
    } catch (err: any) {
      alert(err.message || "Failed to reject leave.");
    }
  };

  // Render Login Layout
  if (!session) {
    return (
      <div className="min-h-screen bg-slate-900 flex items-center justify-center p-4">
        <div className="bg-slate-800 rounded-2xl shadow-xl w-full max-w-md p-8 border border-slate-700">
          <div className="flex flex-col items-center mb-6">
            <div className="w-16 h-16 bg-blue-600 rounded-2xl flex items-center justify-center text-white font-bold text-3xl shadow-lg shadow-blue-500/20 mb-3">
              DF
            </div>
            <h1 className="text-2xl font-bold text-white">Dayflow HRMS</h1>
            <p className="text-slate-400 text-sm mt-1">
              {isSignUp ? 'Create your employee profile' : 'Sign in to your dashboard'}
            </p>
          </div>

          {authError && (
            <div className="bg-red-500/10 border border-red-500/20 text-red-400 text-sm p-3 rounded-lg flex items-center gap-2 mb-6">
              <AlertCircle className="w-4 h-4 flex-shrink-0" />
              <span>{authError}</span>
            </div>
          )}

          {isSignUp ? (
            <form onSubmit={handleSignUp} className="space-y-4">
              <div>
                <label className="block text-slate-300 text-xs font-medium mb-1.5">Full Name</label>
                <input 
                  type="text" 
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={signUpName}
                  onChange={(e) => setSignUpName(e.target.value)}
                  placeholder="e.g. John Doe"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 text-xs font-medium mb-1.5">Email / Login</label>
                <input 
                  type="email" 
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={signUpEmail}
                  onChange={(e) => setSignUpEmail(e.target.value)}
                  placeholder="e.g. john@dayflow.com"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 text-xs font-medium mb-1.5">Password</label>
                <input 
                  type="password" 
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={signUpPassword}
                  onChange={(e) => setSignUpPassword(e.target.value)}
                  placeholder="••••••••"
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 text-xs font-medium mb-1.5">Designated HR Role</label>
                <select 
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={signUpRole}
                  onChange={(e) => setSignUpRole(e.target.value as any)}
                >
                  <option value="employee">Employee (View self logs only)</option>
                  <option value="hr_officer">HR Officer (Manage leaves & view stats)</option>
                  <option value="admin">Administrator (Full dashboard CRUD)</option>
                </select>
              </div>

              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg py-2.5 mt-2 transition-colors shadow-lg shadow-blue-600/15 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating Profile...' : 'Sign Up'}
              </button>
            </form>
          ) : (
            <form onSubmit={handleLogin} className="space-y-4">
              <div>
                <label className="block text-slate-300 text-xs font-medium mb-1.5">Username / Email</label>
                <input 
                  type="text" 
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={loginVal}
                  onChange={(e) => setLoginVal(e.target.value)}
                  required
                />
              </div>

              <div>
                <label className="block text-slate-300 text-xs font-medium mb-1.5">Password</label>
                <input 
                  type="password" 
                  className="w-full bg-slate-700 border border-slate-600 text-white rounded-lg px-4 py-2 text-sm focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500"
                  value={passwordVal}
                  onChange={(e) => setPasswordVal(e.target.value)}
                  required
                />
              </div>

              <button 
                type="submit" 
                disabled={loading}
                className="w-full bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg py-2.5 mt-2 transition-colors shadow-lg shadow-blue-600/15 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Authenticating...' : 'Sign In'}
              </button>
            </form>
          )}

          <div className="mt-6 pt-4 border-t border-slate-700/50 text-center">
            <button 
              onClick={() => {
                setIsSignUp(!isSignUp);
                setAuthError('');
              }}
              className="text-blue-400 hover:text-blue-300 text-xs font-semibold"
            >
              {isSignUp ? 'Already have an account? Sign In' : "Don't have an account? Sign Up"}
            </button>
          </div>

          {!isSignUp && (
            <div className="mt-6 text-center text-xs text-slate-500 space-y-1">
              <p className="font-medium text-slate-400">Demo Credentials:</p>
              <p>Admin: admin / admin</p>
              <p>HR: hr_user / hrpwd</p>
              <p>Employee: emp_user / emppwd</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // Analytics Helpers
  const totalWorkedHours = attendances.reduce((acc, curr) => acc + curr.worked_hours, 0);
  const avgWorkedHours = attendances.length ? (totalWorkedHours / attendances.length) : 0;
  const pendingLeavesCount = leaves.filter(l => l.state === 'pending').length;

  // Chart Data preparation
  const chartData = attendances.slice(0, 10).reverse().map(a => ({
    name: a.date.substring(5), // MM-DD
    hours: parseFloat(a.worked_hours.toFixed(2)),
  }));

  const leaveChartData = [
    { name: 'Sick', balance: 5 },
    { name: 'Casual', balance: 7 },
    { name: 'Earned', balance: 12 },
  ];

  return (
    <div className="min-h-screen bg-slate-50 flex">
      {/* Sidebar navigation */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col flex-shrink-0">
        <div className="p-6 border-b border-slate-800 flex items-center gap-3">
          <div className="w-10 h-10 bg-blue-600 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-lg">
            DF
          </div>
          <div>
            <h1 className="text-white font-bold leading-none">Dayflow</h1>
            <span className="text-xs text-slate-500 font-medium">HR Management</span>
          </div>
        </div>

        {/* User Card */}
        <div className="p-4 border-b border-slate-800/50 bg-slate-950/20 m-4 rounded-xl">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 bg-slate-800 rounded-full flex items-center justify-center text-slate-300">
              <User className="w-5 h-5" />
            </div>
            <div>
              <p className="text-slate-200 text-sm font-semibold truncate max-w-[130px]">{session.username}</p>
              <div className="flex items-center gap-1.5 mt-0.5">
                <Shield className="w-3.5 h-3.5 text-blue-500" />
                <span className="text-slate-500 text-[10px] uppercase font-bold tracking-wider">{session.employee.role}</span>
              </div>
            </div>
          </div>

          {/* Quick Check-In Widget */}
          <div className="mt-4 pt-3 border-t border-slate-800/50">
            <div className="flex flex-col mb-2">
              <div className="flex items-center justify-between">
                <span className="text-slate-400 text-xs">Status:</span>
                <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${isCheckedIn ? 'bg-green-500/10 text-green-400' : 'bg-amber-500/10 text-amber-400'}`}>
                  {isCheckedIn ? 'Checked In' : 'Checked Out'}
                </span>
              </div>
              {isCheckedIn && todayRecord && todayRecord.check_in && (
                <span className="text-[10px] text-slate-500 mt-1 text-right">
                  In: {new Date(todayRecord.check_in).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
            </div>

            <div className="space-y-2">
              <input 
                type="text" 
                placeholder="Log notes/remarks..." 
                className="w-full text-xs bg-slate-800 border border-slate-700 rounded p-1.5 text-white focus:outline-none focus:border-blue-500"
                value={remarks}
                onChange={(e) => setRemarks(e.target.value)}
              />
              <button
                onClick={isCheckedIn ? handleCheckOut : handleCheckIn}
                className={`w-full text-xs font-semibold py-2 px-3 rounded flex items-center justify-center gap-2 transition-colors ${isCheckedIn ? 'bg-rose-600 hover:bg-rose-500 text-white' : 'bg-green-600 hover:bg-green-500 text-white'}`}
              >
                <Clock className="w-3.5 h-3.5" />
                <span>{isCheckedIn ? 'Check Out' : 'Check In'}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Sidebar Tabs */}
        <nav className="flex-1 px-4 space-y-1">
          <button 
            onClick={() => setActiveTab('dashboard')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'dashboard' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
          >
            <BarChart2 className="w-4 h-4" />
            <span>Dashboard</span>
          </button>
          
          <button 
            onClick={() => setActiveTab('attendance')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'attendance' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
          >
            <Clock className="w-4 h-4" />
            <span>Attendance</span>
          </button>

          <button 
            onClick={() => setActiveTab('leaves')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'leaves' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
          >
            <Calendar className="w-4 h-4" />
            <span>Leaves</span>
          </button>

          <button 
            onClick={() => setActiveTab('payroll')}
            className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'payroll' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
          >
            <DollarSign className="w-4 h-4" />
            <span>Payroll</span>
          </button>

          {session.employee.role !== 'employee' && (
            <button 
              onClick={() => setActiveTab('insights')}
              className={`w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold transition-colors ${activeTab === 'insights' ? 'bg-blue-600 text-white' : 'text-slate-400 hover:bg-slate-800 hover:text-slate-200'}`}
            >
              <Brain className="w-4 h-4" />
              <span>AI Insights</span>
            </button>
          )}
        </nav>

        {/* Logout */}
        <div className="p-4 border-t border-slate-800">
          <button 
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 text-slate-400 hover:text-white hover:bg-rose-900/20 py-2.5 rounded-lg text-sm font-semibold transition-colors"
          >
            <LogOut className="w-4 h-4" />
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <header className="bg-white border-b border-slate-200 px-8 py-4 flex items-center justify-between flex-shrink-0">
          <div>
            <h2 className="text-xl font-bold text-slate-800 capitalize">{activeTab}</h2>
            <p className="text-slate-400 text-xs mt-0.5">Welcome back, {session.employee.name}</p>
          </div>
          <div className="text-slate-500 text-xs font-semibold bg-slate-100 px-3 py-1.5 rounded-lg border border-slate-200">
            {new Date().toLocaleDateString('en-US', { weekday: 'long', year: 'numeric', month: 'long', day: 'numeric' })}
          </div>
        </header>

        <div className="p-8 space-y-8 flex-1">
          {/* Active Tab rendering */}
          {activeTab === 'dashboard' && (
            <>
              {/* Quick Summary Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-white rounded-xl border border-slate-200 p-6 flex items-center justify-between shadow-sm">
                  <div>
                    <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Worked Hours</span>
                    <h3 className="text-2xl font-black text-slate-800 mt-1">{totalWorkedHours.toFixed(1)} hrs</h3>
                    <p className="text-xs text-slate-500 mt-0.5">Avg: {avgWorkedHours.toFixed(1)} hrs per log</p>
                  </div>
                  <div className="w-12 h-12 bg-blue-50 text-blue-600 rounded-xl flex items-center justify-center">
                    <Clock className="w-6 h-6" />
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-6 flex items-center justify-between shadow-sm">
                  <div>
                    <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Leave Balance</span>
                    <h3 className="text-2xl font-black text-slate-800 mt-1">24 days</h3>
                    <p className="text-xs text-slate-500 mt-0.5">{pendingLeavesCount} pending approval</p>
                  </div>
                  <div className="w-12 h-12 bg-amber-50 text-amber-600 rounded-xl flex items-center justify-center">
                    <Calendar className="w-6 h-6" />
                  </div>
                </div>

                <div className="bg-white rounded-xl border border-slate-200 p-6 flex items-center justify-between shadow-sm">
                  <div>
                    <span className="text-slate-400 text-xs font-semibold uppercase tracking-wider">Net Salary Pay</span>
                    <h3 className="text-2xl font-black text-slate-800 mt-1">
                      {payrolls.length > 0 ? `$${payrolls[0].net_salary.toLocaleString()}` : '$0.00'}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">Last calculated pay slip</p>
                  </div>
                  <div className="w-12 h-12 bg-emerald-50 text-emerald-600 rounded-xl flex items-center justify-center">
                    <DollarSign className="w-6 h-6" />
                  </div>
                </div>
              </div>

              {/* Charts grid */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Worked hours per day */}
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                  <h3 className="font-bold text-slate-800 mb-4">Worked Hours Trend</h3>
                  <div className="h-64">
                    {chartData.length > 0 ? (
                      <ResponsiveContainer width="100%" height="100%">
                        <AreaChart data={chartData}>
                          <defs>
                            <linearGradient id="colorHours" x1="0" y1="0" x2="0" y2="1">
                              <stop offset="5%" stopColor="#2563eb" stopOpacity={0.2}/>
                              <stop offset="95%" stopColor="#2563eb" stopOpacity={0}/>
                            </linearGradient>
                          </defs>
                          <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                          <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                          <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                          <Tooltip />
                          <Area type="monotone" dataKey="hours" stroke="#2563eb" strokeWidth={2} fillOpacity={1} fill="url(#colorHours)" />
                        </AreaChart>
                      </ResponsiveContainer>
                    ) : (
                      <div className="h-full flex items-center justify-center text-slate-400 text-sm">
                        No recent attendance logs available to chart.
                      </div>
                    )}
                  </div>
                </div>

                {/* Leave balances */}
                <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                  <h3 className="font-bold text-slate-800 mb-4">Leave Balances (Days)</h3>
                  <div className="h-64">
                    <ResponsiveContainer width="100%" height="100%">
                      <BarChart data={leaveChartData}>
                        <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                        <XAxis dataKey="name" stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <YAxis stroke="#94a3b8" fontSize={12} tickLine={false} axisLine={false} />
                        <Tooltip />
                        <Bar dataKey="balance" fill="#f59e0b" radius={[4, 4, 0, 0]} barSize={40} />
                      </BarChart>
                    </ResponsiveContainer>
                  </div>
                </div>
              </div>

              {/* Recent Logs Table */}
              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
                  <h3 className="font-bold text-slate-800">Recent Attendance Logs</h3>
                  <button onClick={() => setActiveTab('attendance')} className="text-blue-600 hover:text-blue-500 text-xs font-semibold">View All</button>
                </div>
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs">
                        <th className="px-6 py-3">Employee</th>
                        <th className="px-6 py-3">Date</th>
                        <th className="px-6 py-3">Check In</th>
                        <th className="px-6 py-3">Check Out</th>
                        <th className="px-6 py-3">Hours</th>
                        <th className="px-6 py-3">Status</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-600">
                      {attendances.slice(0, 5).map(att => (
                        <tr key={att.id} className="hover:bg-slate-50/50">
                          <td className="px-6 py-3.5 font-medium text-slate-800">{att.employee_name}</td>
                          <td className="px-6 py-3.5">{att.date}</td>
                          <td className="px-6 py-3.5">{att.check_in ? new Date(att.check_in).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '-'}</td>
                          <td className="px-6 py-3.5">{att.check_out ? new Date(att.check_out).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'}) : '-'}</td>
                          <td className="px-6 py-3.5 font-semibold text-slate-700">{att.worked_hours.toFixed(2)}</td>
                          <td className="px-6 py-3.5">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              att.status === 'present' ? 'bg-green-100 text-green-700' :
                              att.status === 'leave' ? 'bg-blue-100 text-blue-700' :
                              'bg-rose-100 text-rose-700'
                            }`}>
                              {att.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </>
          )}

          {activeTab === 'attendance' && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="font-bold text-slate-800">Attendance Log History</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs">
                      <th className="px-6 py-3">Employee</th>
                      <th className="px-6 py-3">Date</th>
                      <th className="px-6 py-3">Check In</th>
                      <th className="px-6 py-3">Check Out</th>
                      <th className="px-6 py-3">Worked Hours</th>
                      <th className="px-6 py-3">Status</th>
                      <th className="px-6 py-3">Remarks</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-600">
                    {attendances.map(att => (
                      <tr key={att.id} className="hover:bg-slate-50/50">
                        <td className="px-6 py-3.5 font-medium text-slate-800">{att.employee_name}</td>
                        <td className="px-6 py-3.5">{att.date}</td>
                        <td className="px-6 py-3.5">{att.check_in ? new Date(att.check_in).toLocaleString() : '-'}</td>
                        <td className="px-6 py-3.5">{att.check_out ? new Date(att.check_out).toLocaleString() : '-'}</td>
                        <td className="px-6 py-3.5 font-semibold text-slate-700">{att.worked_hours.toFixed(2)}</td>
                        <td className="px-6 py-3.5">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            att.status === 'present' ? 'bg-green-100 text-green-700' :
                            att.status === 'leave' ? 'bg-blue-100 text-blue-700' :
                            'bg-rose-100 text-rose-700'
                          }`}>
                            {att.status}
                          </span>
                        </td>
                        <td className="px-6 py-3.5 text-slate-400 italic text-xs">{att.remarks || '-'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'leaves' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="font-bold text-slate-800 text-lg">Leave Operations</h3>
                {session.employee.role === 'employee' && (
                  <button 
                    onClick={() => setShowLeaveModal(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white font-semibold rounded-lg px-4 py-2 flex items-center gap-2 text-sm transition-colors shadow-lg shadow-blue-600/10"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Request Leave</span>
                  </button>
                )}
              </div>

              <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm border-collapse">
                    <thead>
                      <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs">
                        <th className="px-6 py-3">Employee</th>
                        <th className="px-6 py-3">Leave Type</th>
                        <th className="px-6 py-3">Start Date</th>
                        <th className="px-6 py-3">End Date</th>
                        <th className="px-6 py-3">Status</th>
                        <th className="px-6 py-3">Approver</th>
                        {session.employee.role !== 'employee' && <th className="px-6 py-3 text-right">Actions</th>}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 text-slate-600">
                      {leaves.map(req => (
                        <tr key={req.id} className="hover:bg-slate-50/50">
                          <td className="px-6 py-3.5 font-medium text-slate-800">{req.employee_name}</td>
                          <td className="px-6 py-3.5 capitalize">{req.leave_type}</td>
                          <td className="px-6 py-3.5">{req.start_date}</td>
                          <td className="px-6 py-3.5">{req.end_date}</td>
                          <td className="px-6 py-3.5">
                            <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                              req.state === 'approved' ? 'bg-green-100 text-green-700' :
                              req.state === 'pending' ? 'bg-amber-100 text-amber-700' :
                              req.state === 'rejected' ? 'bg-rose-100 text-rose-700' :
                              'bg-slate-100 text-slate-700'
                            }`}>
                              {req.state}
                            </span>
                            {req.rejection_reason && (
                              <p className="text-[10px] text-red-500 mt-0.5 truncate max-w-[150px]" title={req.rejection_reason}>
                                Reason: {req.rejection_reason}
                              </p>
                            )}
                          </td>
                          <td className="px-6 py-3.5">{req.approver_name || '-'}</td>
                          {session.employee.role !== 'employee' && (
                            <td className="px-6 py-3.5 text-right space-x-2">
                              {req.state === 'pending' ? (
                                <>
                                  <button 
                                    onClick={() => handleLeaveApprove(req.id)}
                                    className="bg-green-500 hover:bg-green-600 text-white text-xs font-bold rounded px-2.5 py-1"
                                  >
                                    Approve
                                  </button>
                                  <button 
                                    onClick={() => setShowRejectModal(req.id)}
                                    className="bg-rose-500 hover:bg-rose-600 text-white text-xs font-bold rounded px-2.5 py-1"
                                  >
                                    Reject
                                  </button>
                                </>
                              ) : (
                                <span className="text-slate-400 text-xs">Processed</span>
                              )}
                            </td>
                          )}
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}

          {activeTab === 'payroll' && (
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
              <div className="px-6 py-4 border-b border-slate-200">
                <h3 className="font-bold text-slate-800">Payroll Logs & Pay slips</h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm border-collapse">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-semibold text-xs">
                      <th className="px-6 py-3">Employee</th>
                      <th className="px-6 py-3">Month / Year</th>
                      <th className="px-6 py-3">Basic Salary</th>
                      <th className="px-6 py-3">Allowances</th>
                      <th className="px-6 py-3">Deductions</th>
                      <th className="px-6 py-3">Net Salary</th>
                      <th className="px-6 py-3">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 text-slate-600">
                    {payrolls.map(pr => (
                      <tr key={pr.id} className="hover:bg-slate-50/50">
                        <td className="px-6 py-3.5 font-medium text-slate-800">{pr.employee_name}</td>
                        <td className="px-6 py-3.5">{pr.payroll_month} / {pr.payroll_year}</td>
                        <td className="px-6 py-3.5">${pr.basic_salary.toLocaleString()}</td>
                        <td className="px-6 py-3.5">${pr.allowances.toLocaleString()}</td>
                        <td className="px-6 py-3.5">${pr.deductions.toLocaleString()}</td>
                        <td className="px-6 py-3.5 font-bold text-slate-800">${pr.net_salary.toLocaleString()}</td>
                        <td className="px-6 py-3.5">
                          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                            pr.state === 'paid' ? 'bg-green-100 text-green-700' :
                            pr.state === 'approved' ? 'bg-blue-100 text-blue-700' :
                            'bg-slate-100 text-slate-700'
                          }`}>
                            {pr.state}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {activeTab === 'insights' && insights && (
            <div className="space-y-8">
              {/* Overlapping leaves alert banner if concurrent department leaves found */}
              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <div className="flex items-center gap-3 mb-4">
                  <Brain className="w-6 h-6 text-blue-600" />
                  <h3 className="font-black text-slate-800 text-lg">AI Analytics & HR Signals</h3>
                </div>
                <p className="text-slate-500 text-sm mb-6">
                  Here are the auto-compiled analytical findings extracted from Odoo. These identify performance gaps, operational threats, and schedule concurrency conflicts dynamically.
                </p>

                <div className="grid grid-cols-1 gap-6">
                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
                    <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                      <AlertCircle className="w-4 h-4 text-red-500" />
                      <span>Late Check-in Violations (&gt; 09:15 AM check-in counts &gt;= 5)</span>
                    </h4>
                    <div className="prose max-w-none text-slate-600 text-sm overflow-x-auto" dangerouslySetInnerHTML={{ __html: insights.late_arrivals_html }} />
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
                    <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                      <AlertTriangle className="w-4 h-4 text-amber-500" />
                      <span>Departmental Leave Concurrency Alerts</span>
                    </h4>
                    <div className="prose max-w-none text-slate-600 text-sm overflow-x-auto" dangerouslySetInnerHTML={{ __html: insights.overlapping_leaves_html }} />
                  </div>

                  <div className="bg-slate-50 border border-slate-200 rounded-xl p-6">
                    <h4 className="font-bold text-slate-700 mb-3 flex items-center gap-2">
                      <BarChart2 className="w-4 h-4 text-blue-500" />
                      <span>Monthly Attendance Percentage Trend</span>
                    </h4>
                    <div className="prose max-w-none text-slate-600 text-sm overflow-x-auto" dangerouslySetInnerHTML={{ __html: insights.department_trends_html }} />
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Leave request modal */}
      {showLeaveModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Request Time Off</h3>
            <form onSubmit={handleLeaveSubmit} className="space-y-4">
              {leaveError && (
                <div className="bg-rose-50 border border-rose-100 text-rose-600 text-xs p-3 rounded-lg flex items-center gap-2">
                  <AlertCircle className="w-4 h-4" />
                  <span>{leaveError}</span>
                </div>
              )}
              
              <div>
                <label className="block text-slate-600 text-xs font-semibold mb-1">Leave Type</label>
                <select 
                  className="w-full border border-slate-200 rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500"
                  value={leaveType}
                  onChange={(e) => setLeaveType(e.target.value as any)}
                >
                  <option value="sick">Sick Leave</option>
                  <option value="casual">Casual Leave</option>
                  <option value="earned">Earned Leave</option>
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-slate-600 text-xs font-semibold mb-1">Start Date</label>
                  <input 
                    type="date" 
                    className="w-full border border-slate-200 rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500"
                    value={leaveStart}
                    onChange={(e) => setLeaveStart(e.target.value)}
                    required
                  />
                </div>
                <div>
                  <label className="block text-slate-600 text-xs font-semibold mb-1">End Date</label>
                  <input 
                    type="date" 
                    className="w-full border border-slate-200 rounded-lg p-2 text-sm focus:outline-none focus:border-blue-500"
                    value={leaveEnd}
                    onChange={(e) => setLeaveEnd(e.target.value)}
                    required
                  />
                </div>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button 
                  type="button" 
                  onClick={() => setShowLeaveModal(false)}
                  className="border border-slate-200 text-slate-500 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button 
                  type="submit" 
                  className="bg-blue-600 hover:bg-blue-500 text-white text-sm font-semibold px-4 py-2 rounded-lg"
                >
                  Submit Request
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Reject Leave reason modal */}
      {showRejectModal !== null && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-xl w-full max-w-md p-6 border border-slate-200">
            <h3 className="text-lg font-bold text-slate-800 mb-4">Reject Leave Request</h3>
            <div className="space-y-4">
              <div>
                <label className="block text-slate-600 text-xs font-semibold mb-1">Rejection Reason</label>
                <textarea 
                  className="w-full border border-slate-200 rounded-lg p-2.5 text-sm focus:outline-none focus:border-blue-500 h-24"
                  placeholder="Provide a constructive reason for rejection..."
                  value={rejectReason}
                  onChange={(e) => setRejectReason(e.target.value)}
                  required
                />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-slate-100">
                <button 
                  type="button" 
                  onClick={() => { setShowRejectModal(null); setRejectReason(''); }}
                  className="border border-slate-200 text-slate-500 text-sm font-semibold px-4 py-2 rounded-lg hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button 
                  onClick={handleLeaveRejectSubmit}
                  className="bg-rose-600 hover:bg-rose-500 text-white text-sm font-semibold px-4 py-2 rounded-lg"
                >
                  Reject Request
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default App;
